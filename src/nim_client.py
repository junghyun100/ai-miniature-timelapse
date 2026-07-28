"""
Async NIM Client for AI Miniature Timelapse v2.0

Implements the NVIDIA NIM constrained wording layer per Section 14.

Key Requirements (Section 14.2-14.6):
- Strict JSON request/response contract (schemas/nim-request.schema.json, nim-response.schema.json)
- Request lifecycle: abort controller, 60s timeout, 2 retries for 429/5xx, stale discard
- Mutable fields only: scenes.*.first_frame_prompt, scenes.*.video_prompt
- Post-NIM normalization via domain.normalize_nim_response()
- Provenance tracking without secrets
- Security: no API keys in logs/errors/exports
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any, Optional

import httpx

from .domain import (
    NimRequest,
    NimResponse,
    NimSceneRequest,
    NimSceneResponse,
    Project,
    Provenance,
    ProvenanceSource,
    normalize_nim_response,
    compute_source_revision,
)

# Configure logging (filter API keys)
_logger = logging.getLogger(__name__)
# Don't add handlers here - let application configure


class NimClientError(Exception):
    """Base exception for NIM client errors."""

    def __init__(self, message: str, status_code: int | None = None, details: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class NimAuthError(NimClientError):
    """Authentication/authorization error (401, 403)."""


class NimBadRequestError(NimClientError):
    """Invalid request (400)."""


class NimNotFoundError(NimClientError):
    """Endpoint not found (404)."""


class NimRateLimitError(NimClientError):
    """Rate limited (429) - retryable."""


class NimServerError(NimClientError):
    """Server error (5xx) - retryable."""


class NimTimeoutError(NimClientError):
    """Request timeout."""


class NimStaleResponseError(NimClientError):
    """Response source_revision doesn't match current draft."""


class NimClient:
    """
    Async client for NVIDIA NIM constrained wording layer.

    Usage:
        client = NimClient(base_url="https://integrate.api.nvidia.com/v1", api_key="...")
        response = await client.rewrite_prompts(project, nim_model_id="meta/llama-3.1-8b-instruct")
    """

    DEFAULT_TIMEOUT = 60.0  # seconds (Section 14.4)
    MAX_RETRIES = 2  # Section 14.4: retry at most twice
    RETRY_BACKOFF_BASE = 1.0  # seconds, exponential

    # Retryable status codes
    RETRYABLE_CODES = {429, 500, 502, 503, 504}
    # Non-retryable - immediate failure
    NON_RETRYABLE_CODES = {400, 401, 403, 404}

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        session_token: str | None = None,
    ):
        """
        Initialize NIM client.

        Args:
            base_url: NIM API base URL (e.g., "https://integrate.api.nvidia.com/v1")
            api_key: NVIDIA API key (or set NIM_API_KEY env var)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for retryable errors
            session_token: Optional per-launch session token for proxy auth
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("NIM_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries
        self.session_token = session_token

        if not self.api_key:
            _logger.warning("No NIM API key provided; client will fail on requests")

        # Build headers (no Authorization in logs)
        self._headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.session_token:
            self._headers["X-Session-Token"] = self.session_token

        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> NimClient:
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Create or return existing HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _build_auth_headers(self) -> dict[str, str]:
        """Build Authorization header (not logged)."""
        headers = self._headers.copy()
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _sanitize_for_log(self, data: Any) -> Any:
        """Remove sensitive fields from data for logging. Recursively scans dicts and lists."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                key_lower = key.lower()
                # Redact known sensitive keys
                if key_lower in ("authorization", "authorizationheader", "api_key", "nim_api_key", "apikey", "secret", "token", "apikey"):
                    sanitized[key] = "***REDACTED***"
                elif key_lower in ("headers", "cookies"):
                    # Special handling for headers/cookies dicts
                    sanitized[key] = self._sanitize_for_log(value)
                else:
                    sanitized[key] = self._sanitize_for_log(value)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_for_log(item) for item in data]
        elif isinstance(data, str):
            res = data
            if self.api_key and self.api_key in res:
                res = res.replace(self.api_key, "***REDACTED***")
            import re
            res = re.sub(r"nvapi-[A-Za-z0-9_-]{10,}", "***REDACTED***", res)
            res = re.sub(r"Bearer\s+[A-Za-z0-9._-]+", "Bearer ***REDACTED***", res, flags=re.IGNORECASE)
            return res
        else:
            return data

    async def rewrite_prompts(
        self,
        project: Project,
        nim_model_id: str,
        request_id: str | None = None,
    ) -> tuple[NimResponse, Provenance]:
        """
        Send prompt rewrite request to NIM.

        Per Section 14.4:
        - Each click creates new request_id and captures source_revision
        - Abort any earlier in-flight request
        - Disable primary button, show progress
        - 60s timeout
        - Retry at most twice for 429/5xx
        - No retry for 400/401/403/404
        - Discard stale/out-of-order responses

        Args:
            project: Canonical Project with local planner prompts
            nim_model_id: NIM model identifier (e.g., "meta/llama-3.1-8b-instruct")
            request_id: Optional caller-provided request ID (generated if None)

        Returns:
            Tuple of (NimResponse, Provenance)

        Raises:
            NimStaleResponseError: If response source_revision doesn't match
            NimAuthError: On 401/403
            NimBadRequestError: On 400
            NimNotFoundError: On 404
            NimServerError: On 5xx after retries exhausted
            NimTimeoutError: On timeout
        """
        # Compute source revision from current project state
        source_revision = project.compute_source_revision()
        req_id = request_id or str(uuid.uuid4())

        # Build NIM request per Section 14.2
        nim_request = self._build_nim_request(project, req_id, source_revision)

        # Validate request against schema
        self._validate_nim_request(nim_request)

        _logger.info(
            "NIM request: request_id=%s, model=%s, scenes=%d",
            req_id, nim_model_id, len(nim_request.scenes)
        )

        # Make request with retry logic
        response_data = await self._post_with_retry(
            endpoint="/chat/completions",
            payload=nim_request.to_dict(),
            request_id=req_id,
        )

        _logger.debug("NIM raw response: %s", self._sanitize_for_log(response_data))

        # Parse response
        nim_response = self._parse_nim_response(response_data, req_id, source_revision)

        # Normalize response per Section 14.5
        local_scenes = [self._project_scene_to_nim(s) for s in project.scenes]
        normalized_response, warnings = normalize_nim_response(
            nim_response, local_scenes, source_revision
        )

        # Build provenance per Section 14.6
        provenance = Provenance(
            source=ProvenanceSource.NIM,
            provider="NVIDIA",
            model_id=nim_model_id,
            base_url_label=self._url_label,
            generated_at=datetime.utcnow(),
            request_id=req_id,
            source_revision=source_revision,
            fallback_scene_ids=[],
            validation_warnings=warnings,
        )

        return normalized_response, provenance

    def _build_nim_request(
        self,
        project: Project,
        request_id: str,
        source_revision: str,
    ) -> NimRequest:
        """Build NimRequest from canonical Project."""
        # Extract subject fields based on genre
        subject = {}
        if project.topic:
            subject["topic"] = project.topic
        if project.genre:
            subject["genre"] = project.genre
        if project.subtype:
            subject["subtype"] = project.subtype
        if project.model_name:
            subject["model_name"] = project.model_name
        if project.dish_name:
            subject["dish_name"] = project.dish_name
        if project.craft_name:
            subject["craft_name"] = project.craft_name

        # Build scene requests
        scenes = []
        for i, scene in enumerate(project.scenes):
            local_ff_prompt = scene.first_frame_prompt or ""
            if i >= 1 and project.workflow_mode.value == "REFERENCE_FRAME_RELAY":
                local_ff_prompt = ""  # Scene 2+ must not have first-frame prompt

            scenes.append(NimSceneRequest(
                id=scene.id,
                name=scene.name,
                start_state=scene.asset_ref.flow_asset_label or f"Scene {scene.id} input",
                ordered_actions=[],  # Not used by NIM
                end_state="",        # Not used by NIM
                local_first_frame_prompt=local_ff_prompt,
                local_video_prompt=scene.video_prompt,
            ))

        return NimRequest(
            request_id=request_id,
            source_revision=source_revision,
            profile={
                "id": project.profile_id,
                "version": project.profile_version,
                "workflow_mode": project.workflow_mode.value,
            },
            subject=subject,
            style_bible=project.style_bible.to_dict() if project.style_bible else {},
            scenes=scenes,
            mutable_fields=[
                "scenes.*.first_frame_prompt",
                "scenes.*.video_prompt",
            ],
            immutable_rules=[
                "Preserve scene count and ordering",
                "Preserve identity lock in all prompts",
                "Preserve hands-only rule: giant human hands only",
                "Preserve camera/lighting/workspace consistency",
                "Scene 1 only may have first_frame_prompt",
                "Negative prompt must remain identical",
                "Template exclusions must remain",
                "Asset handoff lineage must not change",
            ],
        )

    def _project_scene_to_nim(self, scene) -> NimSceneRequest:
        """Convert canonical Scene to NimSceneRequest for fallback."""
        local_ff = scene.first_frame_prompt or ""
        return NimSceneRequest(
            id=scene.id,
            name=scene.name,
            start_state="",
            ordered_actions=[],
            end_state="",
            local_first_frame_prompt=local_ff,
            local_video_prompt=scene.video_prompt,
        )

    def _validate_nim_request(self, request: NimRequest) -> None:
        """Basic validation of NIM request before sending."""
        if request.schema_version != "2.0":
            raise ValueError(f"Invalid schema_version: {request.schema_version}")
        if not request.request_id:
            raise ValueError("request_id is required")
        if not request.source_revision or not request.source_revision.startswith("sha256:"):
            raise ValueError(f"Invalid source_revision: {request.source_revision}")
        if not request.scenes:
            raise ValueError("At least one scene required")
        for scene in request.scenes:
            if scene.id < 1:
                raise ValueError(f"Invalid scene id: {scene.id}")

    async def _post_with_retry(
        self,
        endpoint: str,
        payload: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        """POST with retry logic per Section 14.4."""
        client = await self._ensure_client()
        url = f"{self.base_url}{endpoint}"
        headers = self._build_auth_headers()

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                _logger.debug("NIM request attempt %d/%d", attempt + 1, self.max_retries + 1)
                response = await client.post(url, json=payload, headers=headers)
                return await self._handle_response(response, request_id)

            except (NimAuthError, NimBadRequestError, NimNotFoundError) as e:
                # Non-retryable - raise immediately
                _logger.error("NIM non-retryable error: %s", e)
                raise

            except (NimRateLimitError, NimServerError, httpx.TimeoutException) as e:
                last_error = e
                if attempt < self.max_retries:
                    wait = self.RETRY_BACKOFF_BASE * (2 ** attempt)
                    _logger.warning("NIM retryable error (attempt %d): %s, waiting %.1fs",
                                   attempt + 1, e, wait)
                    await asyncio.sleep(wait)
                    continue
                # Retries exhausted
                break

            except httpx.RequestError as e:
                # Network error - retry
                last_error = e
                if attempt < self.max_retries:
                    wait = self.RETRY_BACKOFF_BASE * (2 ** attempt)
                    _logger.warning("NIM network error (attempt %d): %s, waiting %.1fs",
                                   attempt + 1, e, wait)
                    await asyncio.sleep(wait)
                    continue
                break

        # All retries exhausted
        if isinstance(last_error, httpx.TimeoutException):
            raise NimTimeoutError(f"Request timed out after {self.timeout}s")
        if isinstance(last_error, NimRateLimitError):
            raise NimRateLimitError(str(last_error), status_code=429)
        if isinstance(last_error, NimServerError):
            raise last_error
        raise NimServerError(f"NIM request failed after {self.max_retries + 1} attempts: {last_error}")

    async def _handle_response(
        self,
        response: httpx.Response,
        expected_request_id: str,
    ) -> dict[str, Any]:
        """Process HTTP response, raise appropriate exceptions."""
        status = response.status_code

        if status == 200:
            try:
                return response.json()
            except json.JSONDecodeError as e:
                raise NimBadRequestError(f"Invalid JSON response: {e}")

        if status == 400:
            raise NimBadRequestError("Bad request", status_code=400, details=response.text)
        if status == 401:
            raise NimAuthError("Unauthorized - invalid API key", status_code=401)
        if status == 403:
            raise NimAuthError("Forbidden - check API key permissions", status_code=403)
        if status == 404:
            raise NimNotFoundError("Endpoint not found", status_code=404)
        if status == 429:
            raise NimRateLimitError("Rate limited", status_code=429, details=response.text)
        if status >= 500:
            raise NimServerError(f"Server error: {status}", status_code=status, details=response.text)

        # Unexpected status
        raise NimClientError(f"Unexpected status: {status}", status_code=status, details=response.text)

    def _parse_nim_response(
        self,
        data: dict[str, Any],
        expected_request_id: str,
        expected_source_revision: str,
    ) -> NimResponse:
        """Parse and validate NIM response."""
        # Check request_id match
        resp_request_id = data.get("request_id")
        if resp_request_id != expected_request_id:
            raise NimStaleResponseError(
                f"Request ID mismatch: expected {expected_request_id}, got {resp_request_id}"
            )

        # Check source_revision match (staleness)
        resp_source_rev = data.get("source_revision")
        if resp_source_rev != expected_source_revision:
            raise NimStaleResponseError(
                f"Source revision mismatch: expected {expected_source_revision}, got {resp_source_rev}"
            )

        # Parse scenes
        scenes = []
        for s in data.get("scenes", []):
            scenes.append(NimSceneResponse(
                id=s["id"],
                first_frame_prompt=s.get("first_frame_prompt", ""),
                video_prompt=s.get("video_prompt", ""),
            ))

        return NimResponse(
            schema_version=data.get("schema_version", "2.0"),
            request_id=resp_request_id,
            source_revision=resp_source_rev,
            scenes=scenes,
        )

    @property
    def _url_label(self) -> str:
        """Human-readable URL label for provenance (no secrets)."""
        if "integrate.api.nvidia.com" in self.base_url:
            return "NVIDIA Integrate API"
        return self.base_url


# Synchronous wrapper for CLI usage
class SyncNimClient:
    """Synchronous wrapper for CLI scripts."""

    def __init__(self, *args, **kwargs):
        self._async_client = NimClient(*args, **kwargs)

    def rewrite_prompts(
        self,
        project: Project,
        nim_model_id: str,
        request_id: str | None = None,
    ) -> tuple[NimResponse, Provenance]:
        """Synchronous wrapper."""
        return asyncio.run(self._async_client.rewrite_prompts(project, nim_model_id, request_id))

    def close(self):
        asyncio.run(self._async_client.close())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience function for simple usage
async def nim_rewrite(
    project: Project,
    base_url: str,
    nim_model_id: str,
    api_key: str | None = None,
) -> tuple[NimResponse, Provenance]:
    """
    One-shot async NIM rewrite.

    Args:
        project: Canonical Project
        base_url: NIM API base URL
        nim_model_id: Model identifier
        api_key: Optional API key (defaults to NIM_API_KEY env)

    Returns:
        (NimResponse, Provenance)
    """
    async with NimClient(base_url=base_url, api_key=api_key) as client:
        return await client.rewrite_prompts(project, nim_model_id)