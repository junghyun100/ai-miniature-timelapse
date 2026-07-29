"""
Fetch Wrapper Module for UI Request Adapter (WP-2)

Implements robust HTTP fetching with 60s client timeout, AbortSignal support,
exponential backoff retries (max 2), and status code handling per Section 14.4.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import httpx

from .error_handling import (
    HttpError,
    RequestAbortedError,
    RequestTimeoutError,
    RetryExhaustedError,
    is_retryable_error,
)

if TYPE_CHECKING:
    from collections.abc import Callable


class FetchWrapper:
    """
    HTTP request wrapper supporting timeout, abort cancellation, exponential retry,
    and error sanitization per Section 14.4.
    """

    DEFAULT_TIMEOUT: float = 60.0
    MAX_RETRIES: int = 2
    RETRY_BACKOFF_BASE: float = 0.1  # Fast backoff for tests / client responsiveness

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        default_timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        backoff_base: float = RETRY_BACKOFF_BASE,
    ):
        self.client = client
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base

    async def fetch_json(
        self,
        url: str,
        method: str = "POST",
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        request_id: int | None = None,
        timeout: float | None = None,
        cancel_event: asyncio.Event | None = None,
        on_retry: Callable[[int, Exception], None] | None = None,
    ) -> dict[str, Any]:
        """
        Execute an HTTP JSON request with timeout, abort cancellation, and retries.
        """
        req_timeout = timeout if timeout is not None else self.default_timeout
        attempt = 0
        last_error: Exception | None = None

        while attempt <= self.max_retries:
            # Check abort before attempt
            if cancel_event and cancel_event.is_set():
                raise RequestAbortedError(
                    f"Request {request_id} was aborted before attempt {attempt + 1}",
                    request_id=request_id,
                )

            try:
                # Wrap request in timeout and cancel event listener
                return await self._single_attempt(
                    url=url,
                    method=method,
                    json_data=json_data,
                    headers=headers,
                    timeout=req_timeout,
                    cancel_event=cancel_event,
                )

            except Exception as err:
                last_error = err

                # Non-retryable errors fail immediately
                if not is_retryable_error(err) or attempt >= self.max_retries:
                    if attempt > 0 and is_retryable_error(err):
                        raise RetryExhaustedError(
                            f"Request failed after {attempt + 1} attempts: {str(err)}",
                            attempts=attempt + 1,
                            last_error=err,
                        ) from err
                    raise

                # Prepare for retry
                attempt += 1
                if on_retry:
                    on_retry(attempt, err)

                # Exponential backoff
                delay = self.backoff_base * (2 ** (attempt - 1))
                try:
                    if cancel_event:
                        # Wait for delay or abort signal
                        await asyncio.wait_for(cancel_event.wait(), timeout=delay)
                        if cancel_event.is_set():
                            raise RequestAbortedError(
                                f"Request {request_id} was aborted during retry delay",
                                request_id=request_id,
                            )
                    else:
                        await asyncio.sleep(delay)
                except TimeoutError:
                    # Delay completed normally, proceed to next attempt
                    pass

        if last_error:
            raise last_error
        raise HttpError("Unknown request failure", status_code=500)

    async def _single_attempt(
        self,
        url: str,
        method: str,
        json_data: dict[str, Any] | None,
        headers: dict[str, str] | None,
        timeout: float,
        cancel_event: asyncio.Event | None,
    ) -> dict[str, Any]:
        """Perform a single HTTP attempt with cancellation and timeout."""
        local_client = self.client or httpx.AsyncClient()
        should_close = self.client is None

        try:
            request_task = asyncio.create_task(
                local_client.request(
                    method=method,
                    url=url,
                    json=json_data,
                    headers=headers,
                    timeout=timeout,
                )
            )

            if cancel_event:
                cancel_task = asyncio.create_task(cancel_event.wait())
                done, pending = await asyncio.wait(
                    [request_task, cancel_task],
                    timeout=timeout,
                    return_when=asyncio.FIRST_COMPLETED,
                )

                for t in pending:
                    t.cancel()

                if cancel_task in done and cancel_event.is_set():
                    request_task.cancel()
                    raise RequestAbortedError("Request was aborted during network call")

                if not done:
                    request_task.cancel()
                    raise RequestTimeoutError(
                        f"Client timeout of {timeout}s exceeded", timeout_seconds=timeout
                    )

                response = await request_task
            else:
                try:
                    response = await asyncio.wait_for(request_task, timeout=timeout)
                except TimeoutError:
                    raise RequestTimeoutError(
                        f"Client timeout of {timeout}s exceeded", timeout_seconds=timeout
                    )

            # Check status code
            if response.status_code >= 400:
                raise HttpError(
                    f"HTTP {response.status_code}: {response.reason_phrase}",
                    status_code=response.status_code,
                    response_body=response.text,
                )

            return response.json()

        finally:
            if should_close:
                await local_client.aclose()
