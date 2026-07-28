"""
State Store Module for UI Request Adapter (WP-2)

Manages request lifecycle states, applied plan persistence, stale guard enforcement,
and state transitions per Section 14.4.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from .error_handling import (
    RequestAbortedError,
    RequestAdapterError,
    RequestTimeoutError,
    StaleResponseError,
)
from .provenance_model import ProvenanceModel


class RequestState(str, Enum):
    IDLE = "IDLE"
    LOADING = "LOADING"
    RETRYING = "RETRYING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    ABORTED = "ABORTED"
    STALE = "STALE"


class StateStore:
    """
    Manages state, canonical plan, and staleness validation for UI request operations.
    """

    def __init__(self):
        self.state: RequestState = RequestState.IDLE
        self.active_request_id: int | None = None
        self.source_revision: str | None = None
        self.retry_count: int = 0
        self.applied_plan: dict[str, Any] | None = None
        self.provenance: ProvenanceModel | None = None
        self.last_error: RequestAdapterError | None = None
        self._is_aborted: bool = False

    def is_busy(self) -> bool:
        """Returns True if a request is currently in flight or retrying."""
        return self.state in (RequestState.LOADING, RequestState.RETRYING)

    def start_request(self, request_id: int, source_revision: str) -> None:
        """
        Initialize a new request. If a previous request was active, it is cancelled.
        """
        self.active_request_id = request_id
        self.source_revision = source_revision
        self.retry_count = 0
        self.last_error = None
        self._is_aborted = False
        self.state = RequestState.LOADING

    def update_retry(self, retry_count: int) -> None:
        """Update state to RETRYING with current attempt count."""
        if self._is_aborted or self.state == RequestState.ABORTED:
            return
        self.retry_count = retry_count
        self.state = RequestState.RETRYING

    def validate_stale_guard(
        self, request_id: int, source_revision: str
    ) -> tuple[bool, str | None]:
        """
        Check if incoming response matches current active request ID and source revision.
        Returns (is_valid, reason).
        """
        if self._is_aborted or self.state == RequestState.ABORTED:
            return False, "Request was aborted"

        if request_id != self.active_request_id:
            return (
                False,
                f"Request ID mismatch: received {request_id}, expected {self.active_request_id}",
            )

        if source_revision != self.source_revision:
            return (
                False,
                f"Source revision mismatch: received {source_revision}, expected {self.source_revision}",
            )

        if self.state not in (RequestState.LOADING, RequestState.RETRYING):
            return False, f"State inactive for response: current state is {self.state}"

        return True, None

    def accept_plan(
        self,
        request_id: int,
        source_revision: str,
        plan: dict[str, Any],
        provenance: ProvenanceModel,
    ) -> dict[str, Any]:
        """
        Stale guard check and atomic plan application.
        If valid: updates applied_plan, provenance, and transitions to SUCCESS.
        If invalid (stale): discards response without overwriting applied_plan!
        """
        is_valid, reason = self.validate_stale_guard(request_id, source_revision)
        if not is_valid:
            self.state = RequestState.STALE
            self.last_error = StaleResponseError(
                f"Stale response discarded: {reason}",
                received_request_id=request_id,
                expected_request_id=self.active_request_id,
                received_revision=source_revision,
                expected_revision=self.source_revision,
            )
            return {"accepted": False, "reason": reason}

        # Atomically apply plan & provenance
        self.applied_plan = plan
        self.provenance = provenance
        self.state = RequestState.SUCCESS
        self.last_error = None
        return {"accepted": True, "reason": None}

    def fail_request(self, request_id: int, error: RequestAdapterError) -> None:
        """
        Record request failure. Ensures aborts are NEVER treated as success,
        and timeouts/errors update state appropriately.
        """
        if request_id != self.active_request_id:
            # Ignore failures from old, inactive requests
            return

        self.last_error = error
        if isinstance(error, RequestAbortedError) or self._is_aborted:
            self.state = RequestState.ABORTED
        elif isinstance(error, RequestTimeoutError):
            self.state = RequestState.ERROR
        else:
            self.state = RequestState.ERROR

    def abort_request(self) -> None:
        """Cancel active request and set state to ABORTED."""
        self._is_aborted = True
        self.state = RequestState.ABORTED
        self.last_error = RequestAbortedError(
            "Request aborted by user or state change",
            request_id=self.active_request_id,
        )

    def reset(self) -> None:
        """Reset state store to IDLE."""
        self.state = RequestState.IDLE
        self.active_request_id = None
        self.source_revision = None
        self.retry_count = 0
        self.applied_plan = None
        self.provenance = None
        self.last_error = None
        self._is_aborted = False
