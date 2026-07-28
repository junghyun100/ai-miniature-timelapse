"""
UI Request Adapter Module (WP-2)

Provides the stabilized UI request adapter integrating monotonic request IDs,
timeout & abort controllers, exponential retry policy, stale guard protection,
and provenance tracking per Section 14.4 and Section 14.6.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Optional, Tuple

from .domain import compute_source_revision
from .error_handling import (
    HttpError,
    RequestAbortedError,
    RequestAdapterError,
    RequestTimeoutError,
    StaleResponseError,
    sanitize_error_message,
)
from .fetch_wrapper import FetchWrapper
from .provenance_model import ProvenanceModel, ProvenanceSource
from .state_store import RequestState, StateStore


class UIRequestAdapter:
    """
    UI Request Adapter for AI Miniature Timelapse v2.0.
    Guarantees that late or out-of-order responses never overwrite newer drafts.
    """

    def __init__(
        self,
        fetch_wrapper: Optional[FetchWrapper] = None,
        state_store: Optional[StateStore] = None,
    ):
        self.fetch_wrapper = fetch_wrapper or FetchWrapper()
        self.state_store = state_store or StateStore()
        self._request_id_counter: int = 0
        self._active_cancel_event: Optional[asyncio.Event] = None
        self._current_draft: Optional[Dict[str, Any]] = None

    def get_next_request_id(self) -> int:
        """Generates a monotonically increasing request ID."""
        self._request_id_counter += 1
        return self._request_id_counter

    def get_loading_state(self) -> RequestState:
        """Returns the current loading state."""
        return self.state_store.state

    def get_applied_plan(self) -> Optional[Dict[str, Any]]:
        """Returns the currently applied canonical plan."""
        return self.state_store.applied_plan

    def get_provenance(self) -> Optional[ProvenanceModel]:
        """Returns the provenance object for the currently applied plan."""
        return self.state_store.provenance

    def cancel_active_request(self) -> None:
        """Aborts any currently active in-flight request."""
        if self._active_cancel_event:
            self._active_cancel_event.set()
        self.state_store.abort_request()

    def on_draft_change(self, new_draft: Dict[str, Any]) -> str:
        """
        Handle Source Draft edit: aborts active in-flight request and returns new source revision.
        """
        if self.state_store.is_busy():
            self.cancel_active_request()
        self._current_draft = new_draft
        return compute_source_revision(new_draft)

    async def execute_request(
        self,
        url: str,
        payload: Dict[str, Any],
        draft: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        model_id: Optional[str] = None,
        base_url_label: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a UI request through the complete lifecycle:
        1. Monotonic request ID generation
        2. Source draft revision calculation
        3. Abort in-flight requests
        4. State transition: LOADING / RETRYING
        5. HTTP fetch with timeout and retries
        6. Stale Guard validation before plan application
        7. Strict failure handling (no post-timeout apply, no abort-as-success, no stale overwrite)
        """
        # 1. Monotonic Request ID
        request_id = self.get_next_request_id()

        # 2. Source Revision calculation
        self._current_draft = draft
        source_revision = compute_source_revision(draft)

        # 3. Abort previous request
        if self.state_store.is_busy():
            self.cancel_active_request()

        # 4. Set up cancellation signal & start state
        cancel_event = asyncio.Event()
        self._active_cancel_event = cancel_event
        self.state_store.start_request(request_id, source_revision)

        # Inject request_id and source_revision into payload
        req_payload = dict(payload)
        req_payload["request_id"] = str(request_id)
        req_payload["source_revision"] = source_revision

        def on_retry_callback(attempt: int, err: Exception) -> None:
            self.state_store.update_retry(attempt)

        try:
            # 5. Fetch
            response_data = await self.fetch_wrapper.fetch_json(
                url=url,
                method="POST",
                json_data=req_payload,
                headers=headers,
                request_id=request_id,
                timeout=timeout,
                cancel_event=cancel_event,
                on_retry=on_retry_callback,
            )

            # Extract response metadata or fallback
            res_req_id = response_data.get("request_id", request_id)
            try:
                res_req_id = int(res_req_id)
            except (ValueError, TypeError):
                res_req_id = request_id

            res_revision = response_data.get("source_revision", source_revision)

            # Build Provenance object
            prov_source = response_data.get("provenance", {}).get("source") if isinstance(response_data.get("provenance"), dict) else None
            if not prov_source:
                prov_source = ProvenanceSource.NIM
            try:
                prov_source = ProvenanceSource(prov_source)
            except ValueError:
                prov_source = ProvenanceSource.NIM

            provenance = ProvenanceModel(
                source=prov_source,
                provider=response_data.get("provider", "nvidia_nim"),
                model_id=model_id or response_data.get("model_id"),
                base_url_label=base_url_label or response_data.get("base_url_label"),
                request_id=request_id,
                source_revision=source_revision,
                fallback_scene_ids=response_data.get("fallback_scene_ids", []),
                validation_warnings=response_data.get("validation_warnings", []),
            )

            # 6. Stale Guard check & Atomic Plan Application
            result = self.state_store.accept_plan(
                request_id=res_req_id,
                source_revision=res_revision,
                plan=response_data,
                provenance=provenance,
            )

            if not result["accepted"]:
                return {
                    "success": False,
                    "stale": True,
                    "reason": result["reason"],
                    "state": self.state_store.state,
                }

            return {
                "success": True,
                "request_id": request_id,
                "source_revision": source_revision,
                "plan": self.state_store.applied_plan,
                "provenance": self.state_store.provenance.to_dict() if self.state_store.provenance else None,
                "state": self.state_store.state,
            }

        except Exception as err:
            # Enforce Failure Rules
            wrapped_error = err if isinstance(err, RequestAdapterError) else RequestAdapterError(str(err))
            self.state_store.fail_request(request_id, wrapped_error)

            return {
                "success": False,
                "error": sanitize_error_message(str(err)),
                "error_type": type(err).__name__,
                "state": self.state_store.state,
            }
        finally:
            if self._active_cancel_event is cancel_event:
                self._active_cancel_event = None
