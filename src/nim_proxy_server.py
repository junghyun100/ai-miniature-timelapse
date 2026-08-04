#!/usr/bin/env python3
"""
NIM Proxy Server - Security Hardened per Section 16.4

The NIM proxy provides a secure loopback HTTP interface for browser UI
to call NVIDIA NIM without exposing API keys to browser memory.

Security Requirements (Section 16.4):
- Binds to 127.0.0.1 by default
- Allowlist only configured loopback UI origins (http://127.0.0.1:4173, http://localhost:4173)
- Never returns Access-Control-Allow-Origin: *
- Validates method, Content-Type, body size (≤1 MiB), JSON schema
- Accepts only configured NVIDIA upstream hosts
- Per-launch session token delivered to local UI, sent in dedicated header
- Environment API key option also requires session token
- Returns sanitized structured errors (no secrets)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import time
from dataclasses import dataclass
from typing import Any

import httpx
import jsonschema  # type: ignore[import-untyped]
from jsonschema import validate

# Try to import uvloop for better performance
try:
    import uvloop  # type: ignore[import-not-found]

    uvloop.install()
except ImportError:
    pass


# ============================================================================
# Configuration
# ============================================================================

PROXY_VERSION = "1.0"


@dataclass
class ProxyConfig:
    """Proxy configuration loaded from environment and CLI."""

    # Server binding
    host: str = "127.0.0.1"
    port: int = 4174

    # CORS - strict allowlist
    allowed_origins: list[str] | None = None

    # Request limits
    max_body_size: int = 1_048_576  # 1 MiB

    # NIM upstream
    upstream_hosts: list[str] | None = None
    default_model: str = "nvidia/nemotron-3-ultra-550b-a55b"
    upstream_timeout: float = 60.0

    # Auth
    require_session_token: bool = True
    env_api_key: str = ""

    def __post_init__(self):
        if self.allowed_origins is None:
            self.allowed_origins = [
                "http://127.0.0.1:4173",
                "http://localhost:4173",
            ]
        if self.upstream_hosts is None:
            self.upstream_hosts = [
                "integrate.api.nvidia.com",
                "api.nvidia.com",
            ]


# Global config (set at startup)
_config: ProxyConfig | None = None
_session_token: str | None = None


def _require_config() -> ProxyConfig:
    """Return the initialized proxy config."""
    if _config is None:
        raise RuntimeError("Proxy config is not initialized")
    return _config


def _parse_allowed_origins_env(raw_value: str | None) -> list[str] | None:
    """Parse ALLOWED_ORIGIN env into a normalized list."""
    if raw_value is None:
        return None
    origins = [origin.strip() for origin in raw_value.split(",") if origin.strip()]
    return origins or None


def _resolve_allowed_origins(cli_allowed_origins: list[str] | None) -> list[str]:
    """Resolve effective allowed origins from CLI first, then env, then defaults."""
    if cli_allowed_origins:
        return cli_allowed_origins
    env_origins = _parse_allowed_origins_env(os.environ.get("ALLOWED_ORIGIN"))
    if env_origins:
        return env_origins
    return ProxyConfig().allowed_origins or []


def _resolve_session_token() -> str:
    """Resolve session token from env override or generate a per-launch token."""
    return os.environ.get("NIM_PROXY_SESSION_TOKEN") or secrets.token_urlsafe(32)


def _init_config_from_env():
    """Initialize config from environment variables when module is imported."""
    global _config, _session_token
    if _config is None:
        _config = ProxyConfig(
            host=os.environ.get("NIM_PROXY_HOST", "127.0.0.1"),
            port=int(os.environ.get("NIM_PROXY_PORT", "4174")),
            allowed_origins=_resolve_allowed_origins(None),
            max_body_size=int(os.environ.get("NIM_PROXY_MAX_BODY", "1048576")),
            upstream_hosts=os.environ.get(
                "NIM_PROXY_UPSTREAM_HOSTS", "integrate.api.nvidia.com,api.nvidia.com"
            ).split(","),
            default_model=os.environ.get(
                "NIM_PROXY_DEFAULT_MODEL", "nvidia/nemotron-3-ultra-550b-a55b"
            ),
            require_session_token=os.environ.get("NIM_PROXY_REQUIRE_TOKEN", "true").lower()
            != "false",
            env_api_key=os.environ.get("NIM_PROXY_ENV_API_KEY", ""),
        )
        _session_token = _resolve_session_token()


# ============================================================================
# Module-level initialization (runs on import for uvicorn)
# ============================================================================

_init_config_from_env()


# ============================================================================
# JSON Schemas (inline for self-contained proxy)
# ============================================================================

NIM_REQUEST_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": [
        "schema_version",
        "request_id",
        "source_revision",
        "profile",
        "subject",
        "style_bible",
        "scenes",
        "mutable_fields",
        "immutable_rules",
    ],
    "properties": {
        "schema_version": {"const": "2.0"},
        "request_id": {"type": "string", "format": "uuid"},
        "source_revision": {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$"},
        "profile": {
            "type": "object",
            "required": ["id", "version", "workflow_mode"],
            "properties": {
                "id": {"type": "string"},
                "version": {"type": "string"},
                "workflow_mode": {
                    "type": "string",
                    "enum": ["REFERENCE_FRAME_RELAY", "SINGLE_CLIP_FROM_MASTER"],
                },
            },
            "additionalProperties": False,
        },
        "subject": {"type": "object", "additionalProperties": True},
        "style_bible": {"type": "object", "additionalProperties": True},
        "scenes": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "id",
                    "name",
                    "start_state",
                    "ordered_actions",
                    "end_state",
                    "local_first_frame_prompt",
                    "local_video_prompt",
                ],
                "properties": {
                    "id": {"type": "integer", "minimum": 1},
                    "name": {"type": "string"},
                    "start_state": {"type": "string"},
                    "ordered_actions": {"type": "array", "items": {"type": "string"}},
                    "end_state": {"type": "string"},
                    "local_first_frame_prompt": {"type": "string"},
                    "local_video_prompt": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
        "mutable_fields": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["scenes.*.first_frame_prompt", "scenes.*.video_prompt"],
            },
            "default": ["scenes.*.first_frame_prompt", "scenes.*.video_prompt"],
        },
        "immutable_rules": {"type": "array", "items": {"type": "string"}},
        "model_id": {"type": "string"},
        "model": {"type": "string"},
    },
    "additionalProperties": False,
}


# ============================================================================
# Error Responses (Sanitized - No Secrets)
# ============================================================================


def redact_text(text: str) -> str:
    """Redact raw API key patterns, Bearer tokens, and secrets from string."""
    if not isinstance(text, str):
        return text
    redacted = re.sub(r"nvapi-[A-Za-z0-9_-]{10,}", "[REDACTED]", text)
    redacted = re.sub(
        r"Bearer\s+[A-Za-z0-9._-]+", "Bearer [REDACTED]", redacted, flags=re.IGNORECASE
    )
    return re.sub(
        r"(?:api[_-]?key|secret|token)\s*=\s*['\"][^'\"]+['\"]",
        "[REDACTED]",
        redacted,
        flags=re.IGNORECASE,
    )


def error_response(status: int, code: str, message: str, details: dict | None = None) -> dict:
    """Create sanitized error response - ensures no raw secrets are leaked."""
    response = {
        "error": {
            "code": redact_text(code),
            "message": redact_text(message),
            "timestamp": time.time(),
        }
    }
    if details:
        # Sanitize details
        safe_details: dict[str, Any] = {}
        for k, v in details.items():
            k_lower = k.lower()
            if k_lower in (
                "authorization",
                "api_key",
                "apikey",
                "nim_api_key",
                "token",
                "secret",
                "x-nim-api-key",
                "x-api-key",
            ):
                safe_details[k] = "[REDACTED]"
            elif isinstance(v, str):
                safe_details[k] = redact_text(v)
            elif isinstance(v, dict):
                safe_details[k] = {
                    dk: (
                        "[REDACTED]"
                        if dk.lower()
                        in (
                            "authorization",
                            "api_key",
                            "apikey",
                            "nim_api_key",
                            "token",
                            "secret",
                            "x-nim-api-key",
                            "x-api-key",
                        )
                        else redact_text(dv)
                        if isinstance(dv, str)
                        else dv
                    )
                    for dk, dv in v.items()
                }
            else:
                safe_details[k] = v
        response["error"]["details"] = safe_details
    return response


# ============================================================================
# Request/Response Helpers
# ============================================================================


async def _send_json(send, status: int, payload: dict):
    """Send JSON response via ASGI send."""
    config = _require_config()
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json; charset=utf-8"),
                (b"content-length", str(len(body)).encode()),
                # CORS - strict allowlist only
                (
                    b"access-control-allow-origin",
                    (
                        config.allowed_origins[0]
                        if config.allowed_origins
                        else "http://127.0.0.1:4173"
                    ).encode(),
                ),
                (b"access-control-allow-headers", b"Content-Type, X-Session-Token"),
                (b"access-control-allow-methods", b"GET, POST, OPTIONS"),
                (b"access-control-allow-credentials", b"true"),
            ],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": body,
        }
    )


def _validate_origin(origin: bytes | None) -> bool:
    """Validate Origin header against allowlist."""
    config = _require_config()
    if not origin:
        return False
    origin_str = origin.decode("latin-1")
    return origin_str in (config.allowed_origins or [])


def _check_session_token(headers: list[tuple[bytes, bytes]]) -> bool:
    """Check X-Session-Token header."""
    config = _require_config()
    if not config.require_session_token:
        return True
    for k, v in headers:
        if k == b"x-session-token":
            return v.decode() == _session_token
    return False


def _sanitize_headers(headers: list[tuple[bytes, bytes]]) -> dict:
    """Remove sensitive headers for logging."""
    sanitized = {}
    for k, v in headers:
        key = k.decode()
        if key.lower() in (
            "authorization",
            "x-session-token",
            "cookie",
            "x-nim-api-key",
            "x-api-key",
        ):
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = v.decode()
    return sanitized


# ============================================================================
# ASGI Application
# ============================================================================


async def app(scope, receive, send):
    """ASGI application entry point."""
    global _config, _session_token
    config = _require_config()

    if scope["type"] != "http":
        await send(
            {
                "type": "http.response.start",
                "status": 500,
                "headers": [(b"content-type", b"text/plain")],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"Only HTTP supported",
            }
        )
        return

    path = scope["path"]
    method = scope["method"]

    # Get headers
    headers = scope["headers"]
    origin = next((v for k, v in headers if k == b"origin"), None)

    # Log request (sanitized)
    print(
        f"[{time.strftime('%H:%M:%S')}] {method} {path} from {origin.decode() if origin else 'unknown'}"
    )

    # Handle preflight
    if method == "OPTIONS":
        if _validate_origin(origin):
            await send(
                {
                    "type": "http.response.start",
                    "status": 204,
                    "headers": [
                        (b"access-control-allow-origin", origin),
                        (b"access-control-allow-headers", b"Content-Type, X-Session-Token"),
                        (b"access-control-allow-methods", b"POST, OPTIONS"),
                        (b"access-control-allow-credentials", b"true"),
                        (b"access-control-max-age", b"86400"),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": b""})
        else:
            await send({"type": "http.response.start", "status": 403, "headers": []})
            await send({"type": "http.response.body", "body": b""})
        return

    # Route: GET /health
    if method == "GET" and path == "/health":
        await _send_json(
            send,
            200,
            {
                "status": "ok",
                "version": PROXY_VERSION,
                "upstream": config.upstream_hosts,
                "default_model": config.default_model,
            },
        )
        return

    # Validate origin
    if not _validate_origin(origin):
        print(f"  -> REJECTED: Origin not in allowlist: {origin.decode() if origin else 'missing'}")
        await _send_json(send, 403, error_response(403, "FORBIDDEN", "Origin not allowed"))
        return

    # Validate session token
    if not _check_session_token(headers):
        print("  -> REJECTED: Invalid or missing session token")
        await _send_json(send, 401, error_response(401, "UNAUTHORIZED", "Invalid session token"))
        return

    # Route: POST /api/nim/rewrite
    if method == "POST" and path == "/api/nim/rewrite":
        await handle_nim_rewrite(scope, receive, send)
        return

    # 404
    await _send_json(send, 404, error_response(404, "NOT_FOUND", f"Path not found: {path}"))


async def handle_nim_rewrite(scope, receive, send):
    """Handle NIM rewrite request with full validation."""
    config = _require_config()
    # Read body with size limit
    body = b""
    while True:
        message = await receive()
        if message["type"] == "http.request":
            body += message.get("body", b"")
            if len(body) > config.max_body_size:
                await _send_json(
                    send,
                    413,
                    error_response(
                        413, "PAYLOAD_TOO_LARGE", f"Body exceeds {config.max_body_size} bytes"
                    ),
                )
                return
            if not message.get("more_body", False):
                break
        elif message["type"] == "http.disconnect":
            return

    # Validate Content-Type
    content_type = None
    for k, v in scope["headers"]:
        if k == b"content-type":
            content_type = v.decode()
            break

    if not content_type or not content_type.startswith("application/json"):
        await _send_json(
            send, 400, error_response(400, "BAD_REQUEST", "Content-Type must be application/json")
        )
        return

    # Parse JSON
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as e:
        await _send_json(send, 400, error_response(400, "INVALID_JSON", f"JSON parse error: {e}"))
        return

    # Validate against NIM request schema
    try:
        validate(instance=payload, schema=NIM_REQUEST_SCHEMA)
    except jsonschema.ValidationError as e:
        await _send_json(send, 400, error_response(400, "SCHEMA_VALIDATION_FAILED", str(e)))
        return

    # Extract validated fields
    request_id = payload["request_id"]
    _ = payload["source_revision"]

    print(f"  -> NIM rewrite: request_id={request_id[:8]}, scenes={len(payload['scenes'])}")

    # Extract optional session API key from headers (session-scoped transmission & rotation support)
    session_api_key = None
    for k, v in scope["headers"]:
        if k.lower() in (b"x-nim-api-key", b"x-api-key"):
            session_api_key = v.decode("latin-1").strip()
            break
        if k.lower() == b"authorization" and v.lower().startswith(b"bearer "):
            session_api_key = v.decode("latin-1")[7:].strip()
            break

    # Forward to NIM upstream
    try:
        result = await forward_to_nim(payload, session_api_key=session_api_key)
    except httpx.TimeoutException:
        await _send_json(
            send, 504, error_response(504, "UPSTREAM_TIMEOUT", "NIM upstream timed out")
        )
        return
    except httpx.HTTPStatusError as e:
        # Sanitize upstream error
        await _send_json(
            send,
            e.response.status_code,
            error_response(
                e.response.status_code,
                "UPSTREAM_ERROR",
                f"Upstream returned {e.response.status_code}",
                {"status": e.response.status_code},
            ),
        )
        return
    except Exception as e:
        print(f"  -> ERROR: {e}")
        await _send_json(send, 500, error_response(500, "INTERNAL_ERROR", "Proxy internal error"))
        return

    # Return successful response
    await _send_json(send, 200, result)


async def forward_to_nim(
    request_payload: dict[str, Any], session_api_key: str | None = None
) -> dict[str, Any]:
    """Forward validated request to NVIDIA NIM upstream."""
    config = _require_config()
    # Determine upstream URL
    upstream_url = os.environ.get(
        "NIM_UPSTREAM_URL", "https://integrate.api.nvidia.com/v1/chat/completions"
    )

    # Validate upstream host
    from urllib.parse import urlparse

    parsed = urlparse(upstream_url)
    if parsed.netloc not in (config.upstream_hosts or []):
        raise ValueError(f"Upstream host {parsed.netloc} not in allowlist")

    # Get API key (session header first, then config/env)
    api_key = (
        session_api_key
        or config.env_api_key
        or os.environ.get("NIM_API_KEY")
        or os.environ.get("NGC_API_KEY")
    )
    if not api_key:
        raise ValueError("No API key configured (set NIM_API_KEY env var)")

    # Model selection: SEPARATE model_id and profile_id
    # profile.id is domain workflow ID (e.g. "architecture.korean")
    # model is NIM LLM model ID (e.g. "meta/llama-3.1-8b-instruct")
    profile_id = request_payload.get("profile", {}).get("id")
    raw_model = request_payload.get("model_id") or request_payload.get("model")
    model_id = config.default_model if not raw_model or raw_model == profile_id else raw_model

    # Build upstream request (NIM uses OpenAI-compatible format)
    upstream_payload = {
        "model": model_id,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a constrained wording assistant for AI video prompt generation. "
                    "Return JSON only. Do not add Markdown fences or commentary. "
                    "Preserve scene IDs and count. Write only mutable fields: "
                    "first_frame_prompt (Scene 1 only) and video_prompt. "
                    "Do not create new first-frame prompts. Do not change duration, subject identity, "
                    "camera, audio, exclusions, or assets. Do not omit physical action order. "
                    "Translate user instructions into natural English before integrating them into "
                    "prompt fields. Romanize Korean proper nouns and identify them in English, for example "
                    "근정전 becomes Geunjeongjeon Hall. Never copy untranslated source text except explicit narration."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(request_payload, separators=(",", ":"), ensure_ascii=False),
            },
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(config.upstream_timeout)) as client:
        response = await client.post(
            upstream_url,
            json=upstream_payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        upstream_data = response.json()

    # Parse NIM response
    # NIM returns OpenAI format: {choices: [{message: {content: "..."}}]}
    content = upstream_data.get("choices", [{}])[0].get("message", {}).get("content", "{}")

    try:
        nim_response: dict[str, Any] = json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON from text
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            nim_response = json.loads(match.group(0))
        else:
            raise ValueError("NIM did not return valid JSON")

    # Validate response schema (basic)
    required = ("schema_version", "request_id", "source_revision", "scenes")
    for field in required:
        if field not in nim_response:
            raise ValueError(f"NIM response missing required field: {field}")

    # Must match request_id and source_revision (staleness check)
    if nim_response["request_id"] != request_payload["request_id"]:
        raise ValueError("Response request_id mismatch (stale/out of order)")

    if nim_response["source_revision"] != request_payload["source_revision"]:
        raise ValueError("Response source_revision mismatch (stale)")

    return nim_response


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Run proxy server with uvicorn."""
    parser = argparse.ArgumentParser(description="NIM Proxy Server (Section 16.4)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4174)
    parser.add_argument("--allowed-origins", nargs="+", default=None)
    parser.add_argument("--max-body-size", type=int, default=1_048_576)
    parser.add_argument(
        "--upstream-hosts", nargs="+", default=["integrate.api.nvidia.com", "api.nvidia.com"]
    )
    parser.add_argument("--default-model", default="nvidia/nemotron-3-ultra-550b-a55b")
    parser.add_argument(
        "--no-session-token",
        action="store_true",
        help="Disable session token requirement (dev only)",
    )
    parser.add_argument("--env-api-key", default="", help="API key from env var name (advanced)")

    args = parser.parse_args()

    global _config, _session_token

    _config = ProxyConfig(
        host=args.host,
        port=args.port,
        allowed_origins=_resolve_allowed_origins(args.allowed_origins),
        max_body_size=args.max_body_size,
        upstream_hosts=args.upstream_hosts,
        default_model=args.default_model,
        require_session_token=not args.no_session_token,
        env_api_key=args.env_api_key,
    )

    # Generate per-launch session token unless env override is provided.
    _session_token = _resolve_session_token()

    print("🔒 NIM Proxy Server Starting")
    print(f"   Bind: {_config.host}:{_config.port}")
    print(f"   Allowed Origins: {_config.allowed_origins}")
    print(f"   Max Body: {_config.max_body_size} bytes")
    print(f"   Upstream Hosts: {_config.upstream_hosts}")
    print(f"   Default Model: {_config.default_model}")
    print(f"   Session Token: {_session_token[:8]}... (required: {_config.require_session_token})")
    print(
        f"   API Key: {'[from env]' if _config.env_api_key or os.environ.get('NIM_API_KEY') else '[NOT SET]'}"
    )

    # Run with uvicorn
    import uvicorn  # type: ignore[import-not-found]

    uvicorn.run(
        "nim_proxy_server:app",
        host=_config.host,
        port=_config.port,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
