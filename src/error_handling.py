"""
Error Handling Module for UI Request Adapter (WP-2)

Defines structured exception types, retryability rules, sanitization,
and error classification per Section 14.4.
"""

from __future__ import annotations

import re
from typing import Any


class RequestAdapterError(Exception):
    """Base exception for all UI request adapter operations."""

    def __init__(self, message: str, details: Any | None = None):
        sanitized_msg = sanitize_error_message(message)
        super().__init__(sanitized_msg)
        self.message = sanitized_msg
        self.details = details


class RequestTimeoutError(RequestAdapterError):
    """Raised when a request exceeds client timeout duration."""

    def __init__(self, message: str, timeout_seconds: float = 60.0, request_id: int | None = None):
        super().__init__(
            message, details={"timeout_seconds": timeout_seconds, "request_id": request_id}
        )
        self.timeout_seconds = timeout_seconds
        self.request_id = request_id


class RequestAbortedError(RequestAdapterError):
    """Raised when an in-flight request is aborted/cancelled."""

    def __init__(self, message: str = "Request was cancelled", request_id: int | None = None):
        super().__init__(message, details={"request_id": request_id})
        self.request_id = request_id


class StaleResponseError(RequestAdapterError):
    """Raised when response request_id or source_revision does not match current active request."""

    def __init__(
        self,
        message: str,
        received_request_id: int | None = None,
        expected_request_id: int | None = None,
        received_revision: str | None = None,
        expected_revision: str | None = None,
    ):
        details = {
            "received_request_id": received_request_id,
            "expected_request_id": expected_request_id,
            "received_revision": received_revision,
            "expected_revision": expected_revision,
        }
        super().__init__(message, details=details)
        self.received_request_id = received_request_id
        self.expected_request_id = expected_request_id
        self.received_revision = received_revision
        self.expected_revision = expected_revision


class HttpError(RequestAdapterError):
    """HTTP error response with status code."""

    def __init__(self, message: str, status_code: int, response_body: str | None = None):
        super().__init__(message, details={"status_code": status_code, "body": response_body})
        self.status_code = status_code
        self.response_body = response_body


class RetryExhaustedError(RequestAdapterError):
    """Raised when maximum retries are exhausted."""

    def __init__(self, message: str, attempts: int, last_error: Exception):
        super().__init__(message, details={"attempts": attempts, "last_error": str(last_error)})
        self.attempts = attempts
        self.last_error = last_error


RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}
NON_RETRYABLE_HTTP_CODES = {400, 401, 403, 404}


def is_retryable_status(status_code: int) -> bool:
    """Check if an HTTP status code is retryable per Section 14.4."""
    return status_code in RETRYABLE_HTTP_CODES


def is_retryable_error(error: Exception) -> bool:
    """
    Check if an exception is retryable per Section 14.4.
    Retryable: 429, 5xx, transient connection errors.
    Non-retryable: 400, 401, 403, 404, timeouts, aborts, stale errors.
    """
    if isinstance(error, (RequestTimeoutError, RequestAbortedError, StaleResponseError)):
        return False
    if isinstance(error, HttpError):
        return is_retryable_status(error.status_code)
    # Generic network or connection error can be retried
    return True


def sanitize_error_message(msg: str) -> str:
    """Remove sensitive API keys or tokens from error messages."""
    if not msg:
        return ""
    # Redact key patterns like nvapi-..., Bearer ..., api_key=...
    msg = re.sub(r"nvapi-[A-Za-z0-9_-]+", "[REDACTED_API_KEY]", msg)
    msg = re.sub(
        r'(?:Bearer|key|token|secret)\s*[:=]\s*["\']?[A-Za-z0-9._-]+["\']?',
        "[REDACTED_SECRET]",
        msg,
        flags=re.IGNORECASE,
    )
    return msg
