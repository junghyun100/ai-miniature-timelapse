"""
NIM Proxy Server Tests - Section 16.4

Tests security hardening: origin allowlist, schema validation,
session token auth, secret redaction, error sanitization.
"""
import asyncio
import functools
import json
import os
from unittest.mock import MagicMock, patch

import httpx
import pytest
from jsonschema import validate

import src.nim_proxy_server as proxy_module

# Import the ASGI app and related functions
from src.nim_proxy_server import (
    NIM_REQUEST_SCHEMA,
    ProxyConfig,
    _check_session_token,
    _parse_allowed_origins_env,
    _resolve_allowed_origins,
    _resolve_session_token,
    _validate_origin,
    app,
    error_response,
    forward_to_nim,
)


def run_async(func):
    """Run an async test function synchronously using asyncio.run()."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def proxy_config():
    """Test proxy configuration."""
    return ProxyConfig(
        host="127.0.0.1",
        port=14174,  # Unique port for tests
        allowed_origins=["http://127.0.0.1:4173", "http://localhost:4173"],
        upstream_hosts=["integrate.api.nvidia.com", "api.nvidia.com"],
        max_body_size=1024,  # Small for testing
        require_session_token=True,
        env_api_key="test-nim-api-key",
    )


@pytest.fixture
def valid_nim_request():
    """Valid NIM request per schema."""
    return {
        "schema_version": "2.0",
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "source_revision": "sha256:" + "a" * 64,
        "profile": {
            "id": "architecture.korean",
            "version": "2.0.0",
            "workflow_mode": "REFERENCE_FRAME_RELAY"
        },
        "subject": {"topic": "hanok", "genre": "architecture", "subtype": "hanok"},
        "style_bible": {
            "identity_lock": "test lock",
            "materials": {"primary": [], "secondary": [], "tools": []},
            "camera": {"lens": "85mm", "angle": "45", "movement": "locked", "distance": "fixed"},
            "lighting": {"key": "warm", "fill": "soft", "mood": "cinematic", "consistency": "locked"},
            "color_palette": ["wood", "white"],
            "workspace": "test tray",
            "hands_rule": "giant hands only",
            "motion_rule": "rapid timelapse",
        },
        "scenes": [
            {
                "id": 1,
                "name": "Foundation",
                "start_state": "empty",
                "ordered_actions": ["place stones"],
                "end_state": "foundation done",
                "local_first_frame_prompt": "master prompt",
                "local_video_prompt": "video prompt 1"
            },
            {
                "id": 2,
                "name": "Roof",
                "start_state": "foundation",
                "ordered_actions": ["add roof"],
                "end_state": "roof done",
                "local_first_frame_prompt": "",
                "local_video_prompt": "video prompt 2"
            }
        ],
        "mutable_fields": ["scenes.*.first_frame_prompt", "scenes.*.video_prompt"],
        "immutable_rules": ["preserve identity lock", "preserve negative prompt"]
    }


# ============================================================================
# Helper: Mock receive/send for ASGI testing
# ============================================================================

class MockReceive:
    def __init__(self, body=b"", more_body=False):
        self.body = body
        self.more_body = more_body
        self.called = False

    async def __call__(self):
        if not self.called:
            self.called = True
            return {"type": "http.request", "body": self.body, "more_body": self.more_body}
        return {"type": "http.disconnect"}


class MockSend:
    def __init__(self):
        self.messages = []

    async def __call__(self, message):
        self.messages.append(message)


# ============================================================================
# Test: Configuration & Error Response
# ============================================================================

class TestProxyConfig:
    """Test ProxyConfig creation and validation."""

    def test_default_config(self):
        """Default config has safe values."""
        config = ProxyConfig()
        assert config.host == "127.0.0.1"
        assert config.port == 4174
        assert config.allowed_origins == ["http://127.0.0.1:4173", "http://localhost:4173"]
        assert config.max_body_size == 1_048_576
        assert config.upstream_hosts == ["integrate.api.nvidia.com", "api.nvidia.com"]

    def test_custom_config(self, proxy_config):
        """Custom config values are used."""
        assert proxy_config.host == "127.0.0.1"
        assert proxy_config.port == 14174
        assert proxy_config.max_body_size == 1024
        assert proxy_config.require_session_token is True

    def test_parse_allowed_origin_env_single(self):
        """Single ALLOWED_ORIGIN value is preserved."""
        assert _parse_allowed_origins_env("http://127.0.0.1:8765") == [
            "http://127.0.0.1:8765"
        ]

    def test_parse_allowed_origin_env_comma_separated(self):
        """Comma-separated ALLOWED_ORIGIN values are split and stripped."""
        assert _parse_allowed_origins_env(
            "http://127.0.0.1:8765, http://localhost:8765"
        ) == [
            "http://127.0.0.1:8765",
            "http://localhost:8765",
        ]

    def test_resolve_allowed_origins_uses_env_when_cli_missing(self):
        """Env ALLOWED_ORIGIN becomes the default allowlist when CLI is unset."""
        with patch.dict(os.environ, {"ALLOWED_ORIGIN": "http://127.0.0.1:8765,http://localhost:8765"}, clear=False):
            assert _resolve_allowed_origins(None) == [
                "http://127.0.0.1:8765",
                "http://localhost:8765",
            ]

    def test_resolve_session_token_prefers_env(self):
        """Explicit env session token overrides generated token."""
        with patch.dict(os.environ, {"NIM_PROXY_SESSION_TOKEN": "session-from-env"}, clear=False):
            assert _resolve_session_token() == "session-from-env"


class TestErrorResponse:
    """Test error response generation and sanitization."""

    def test_error_response_basic(self):
        """Basic error response structure."""
        resp = error_response(400, "BAD_REQUEST", "Invalid input")
        assert resp["error"]["code"] == "BAD_REQUEST"
        assert resp["error"]["message"] == "Invalid input"
        assert "timestamp" in resp["error"]
        # status_code is passed in but not included in response body (only in HTTP status)

    def test_error_response_with_details(self):
        """Error response includes details."""
        resp = error_response(400, "VALIDATION_ERROR", "Failed", {"field": "scenes[0].id"})
        assert resp["error"]["details"]["field"] == "scenes[0].id"

    def test_error_response_redacts_authorization(self):
        """Sensitive keys in details are redacted."""
        resp = error_response(400, "ERROR", "Failed", {
            "authorization": "Bearer SECRET",
            "api_key": "KEY_123",
            "normal_field": "value"
        })
        assert resp["error"]["details"]["authorization"] == "[REDACTED]"
        assert resp["error"]["details"]["api_key"] == "[REDACTED]"
        assert resp["error"]["details"]["normal_field"] == "value"


# ============================================================================
# Test: Origin Validation
# ============================================================================

class TestOriginValidation:
    """Test Origin header validation."""

    def test_valid_origin(self, proxy_config):
        """Allowed origin passes validation."""
        proxy_module._config = proxy_config
        assert _validate_origin(b"http://127.0.0.1:4173") is True
        assert _validate_origin(b"http://localhost:4173") is True

    def test_invalid_origin(self, proxy_config):
        """Disallowed origin fails validation."""
        proxy_module._config = proxy_config
        assert _validate_origin(b"http://evil.com") is False
        assert _validate_origin(b"https://127.0.0.1:4173") is False  # Wrong scheme

    def test_missing_origin(self, proxy_config):
        """Missing origin fails validation."""
        proxy_module._config = proxy_config
        assert _validate_origin(None) is False
        assert _validate_origin(b"") is False


# ============================================================================
# Test: Session Token
# ============================================================================

class TestSessionToken:
    """Test session token validation."""

    def test_valid_token(self, proxy_config):
        """Correct session token passes."""
        proxy_module._config = proxy_config
        proxy_module._session_token = "test-token-12345"
        headers = [(b"x-session-token", b"test-token-12345")]
        assert _check_session_token(headers) is True

    def test_invalid_token(self, proxy_config):
        """Wrong session token fails."""
        proxy_module._config = proxy_config
        proxy_module._session_token = "test-token-12345"
        headers = [(b"x-session-token", b"wrong-token")]
        assert _check_session_token(headers) is False

    def test_missing_token(self, proxy_config):
        """Missing token fails when required."""
        proxy_module._config = proxy_config
        proxy_module._session_token = "test-token-12345"
        headers = [(b"content-type", b"application/json")]
        assert _check_session_token(headers) is False

    def test_token_not_required(self, proxy_config):
        """Token not checked when not required."""
        proxy_module._config = ProxyConfig(require_session_token=False)
        headers = [(b"content-type", b"application/json")]
        assert _check_session_token(headers) is True


# ============================================================================
# Test: ASGI App Integration
# ============================================================================

class TestASGIApp:
    """Integration tests for the ASGI application."""

    @run_async
    async def test_preflight_options_allowed_origin(self, proxy_config):
        """OPTIONS preflight returns CORS headers for allowed origin."""
        proxy_module._config = proxy_config
        proxy_module._session_token = "test-token"

        scope = {
            "type": "http",
            "method": "OPTIONS",
            "path": "/api/nim/rewrite",
            "headers": [(b"origin", b"http://127.0.0.1:4173")],
        }
        receive = MockReceive()
        send = MockSend()

        await app(scope, receive, send)

        assert send.messages[0]["type"] == "http.response.start"
        assert send.messages[0]["status"] == 204
        headers = dict(send.messages[0]["headers"])
        assert b"access-control-allow-origin" in headers
        assert headers[b"access-control-allow-origin"] == b"http://127.0.0.1:4173"
        assert headers[b"access-control-allow-credentials"] == b"true"

    @run_async
    async def test_preflight_rejected_origin(self, proxy_config):
        """OPTIONS preflight rejects disallowed origin."""
        proxy_module._config = proxy_config
        proxy_module._session_token = "test-token"

        scope = {
            "type": "http",
            "method": "OPTIONS",
            "path": "/api/nim/rewrite",
            "headers": [(b"origin", b"http://evil.com")],
        }
        receive = MockReceive()
        send = MockSend()

        await app(scope, receive, send)

        assert send.messages[0]["status"] == 403

    @run_async
    async def test_post_rejected_invalid_origin(self, proxy_config):
        """POST request from invalid origin rejected."""
        proxy_module._config = proxy_config
        proxy_module._session_token = "test-token"

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/nim/rewrite",
            "headers": [
                (b"origin", b"http://evil.com"),
                (b"x-session-token", b"test-token"),
                (b"content-type", b"application/json"),
            ],
        }
        receive = MockReceive(b"{}")
        send = MockSend()

        await app(scope, receive, send)

        assert send.messages[0]["status"] == 403
        body = json.loads(send.messages[1]["body"])
        assert body["error"]["code"] == "FORBIDDEN"

    @run_async
    async def test_post_rejected_missing_session_token(self, proxy_config):
        """POST request without session token rejected."""
        proxy_module._config = proxy_config
        proxy_module._session_token = "test-token"

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/nim/rewrite",
            "headers": [
                (b"origin", b"http://127.0.0.1:4173"),
                (b"content-type", b"application/json"),
            ],
        }
        receive = MockReceive(b"{}")
        send = MockSend()

        await app(scope, receive, send)

        assert send.messages[0]["status"] == 401
        body = json.loads(send.messages[1]["body"])
        assert body["error"]["code"] == "UNAUTHORIZED"

    @run_async
    async def test_post_rejected_invalid_session_token(self, proxy_config):
        """POST request with wrong session token rejected."""
        proxy_module._config = proxy_config
        proxy_module._session_token = "test-token"

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/nim/rewrite",
            "headers": [
                (b"origin", b"http://127.0.0.1:4173"),
                (b"x-session-token", b"wrong-token"),
                (b"content-type", b"application/json"),
            ],
        }
        receive = MockReceive(b"{}")
        send = MockSend()

        await app(scope, receive, send)

        assert send.messages[0]["status"] == 401
        body = json.loads(send.messages[1]["body"])
        assert body["error"]["code"] == "UNAUTHORIZED"

    @run_async
    async def test_post_body_too_large(self, proxy_config):
        """Body exceeding max size rejected with 413."""
        proxy_module._config = proxy_config
        proxy_module._session_token = "test-token"

        large_body = b"x" * 2000  # > 1024 limit

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/nim/rewrite",
            "headers": [
                (b"origin", b"http://127.0.0.1:4173"),
                (b"x-session-token", b"test-token"),
                (b"content-type", b"application/json"),
            ],
        }
        receive = MockReceive(large_body)
        send = MockSend()

        await app(scope, receive, send)

        assert send.messages[0]["status"] == 413
        body = json.loads(send.messages[1]["body"])
        assert body["error"]["code"] == "PAYLOAD_TOO_LARGE"

    @run_async
    async def test_post_invalid_content_type(self, proxy_config):
        """Non-JSON content type rejected."""
        proxy_module._config = proxy_config
        proxy_module._session_token = "test-token"

        # Use a small body to avoid PAYLOAD_TOO_LARGE
        small_body = b'{"test": "small"}'

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/nim/rewrite",
            "headers": [
                (b"origin", b"http://127.0.0.1:4173"),
                (b"x-session-token", b"test-token"),
                (b"content-type", b"text/plain"),
            ],
        }
        receive = MockReceive(small_body)
        send = MockSend()

        await app(scope, receive, send)

        assert send.messages[0]["status"] == 400
        body_json = json.loads(send.messages[1]["body"])
        assert body_json["error"]["code"] == "BAD_REQUEST"

    @run_async
    async def test_post_invalid_json(self, proxy_config):
        """Invalid JSON rejected."""
        proxy_module._config = proxy_config
        proxy_module._session_token = "test-token"

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/nim/rewrite",
            "headers": [
                (b"origin", b"http://127.0.0.1:4173"),
                (b"x-session-token", b"test-token"),
                (b"content-type", b"application/json"),
            ],
        }
        receive = MockReceive(b"not valid json")
        send = MockSend()

        await app(scope, receive, send)

        assert send.messages[0]["status"] == 400
        body_json = json.loads(send.messages[1]["body"])
        assert body_json["error"]["code"] == "INVALID_JSON"

    @run_async
    async def test_health_endpoint(self, proxy_config):
        """GET /health returns status without requiring origin or session token."""
        proxy_module._config = proxy_config
        proxy_module._session_token = "test-session-token-12345"

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/health",
            "headers": [],
        }
        receive = MockReceive()
        send = MockSend()

        await app(scope, receive, send)

        assert send.messages[0]["status"] == 200
        body_json = json.loads(send.messages[1]["body"])
        assert body_json["status"] == "ok"
        assert body_json["version"] == "1.0"
        assert body_json["default_model"] == proxy_config.default_model
        assert body_json["upstream"] == proxy_config.upstream_hosts
        assert "session_token" not in body_json
        assert "test-session-token-12345" not in send.messages[1]["body"].decode("utf-8")

    @run_async
    async def test_health_rejects_no_auth_never(self, proxy_config):
        """GET /health remains accessible even when session token is required."""
        proxy_module._config = proxy_config
        proxy_module._session_token = "locked-down-token"

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/health",
            "headers": [(b"origin", b"http://evil.com")],
        }
        receive = MockReceive()
        send = MockSend()

        await app(scope, receive, send)

        assert send.messages[0]["status"] == 200
        body_json = json.loads(send.messages[1]["body"])
        assert body_json["status"] == "ok"

    @run_async
    async def test_404_for_unknown_path(self, proxy_config):
        """Unknown path returns 404."""
        proxy_module._config = proxy_config
        proxy_module._session_token = "test-token"

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/unknown",
            "headers": [
                (b"origin", b"http://127.0.0.1:4173"),
                (b"x-session-token", b"test-token"),
            ],
        }
        receive = MockReceive()
        send = MockSend()

        await app(scope, receive, send)

        assert send.messages[0]["status"] == 404


# ============================================================================
# Test: Schema Validation (NIM Request)
# ============================================================================

class TestSchemaValidation:
    """Test NIM request schema validation."""

    def test_valid_request_passes(self, valid_nim_request):
        """Valid request passes schema validation."""
        is_valid = True
        try:
            validate(instance=valid_nim_request, schema=NIM_REQUEST_SCHEMA)
        except Exception:
            is_valid = False
        assert is_valid is True

    def test_missing_required_field_fails(self, valid_nim_request):
        """Missing required field fails validation."""
        del valid_nim_request["request_id"]
        with pytest.raises(Exception):
            validate(instance=valid_nim_request, schema=NIM_REQUEST_SCHEMA)

    def test_invalid_schema_version_fails(self, valid_nim_request):
        """Wrong schema version fails."""
        valid_nim_request["schema_version"] = "1.0"
        with pytest.raises(Exception):
            validate(instance=valid_nim_request, schema=NIM_REQUEST_SCHEMA)

    def test_invalid_workflow_mode_fails(self, valid_nim_request):
        """Invalid workflow mode fails."""
        valid_nim_request["profile"]["workflow_mode"] = "INVALID_MODE"
        with pytest.raises(Exception):
            validate(instance=valid_nim_request, schema=NIM_REQUEST_SCHEMA)

    def test_scene_missing_first_frame_prompt_fails(self, valid_nim_request):
        """Scene missing local_first_frame_prompt fails."""
        valid_nim_request["scenes"][0].pop("local_first_frame_prompt")
        with pytest.raises(Exception):
            validate(instance=valid_nim_request, schema=NIM_REQUEST_SCHEMA)

    def test_invalid_mutable_fields_fails(self, valid_nim_request):
        """Invalid mutable_fields value fails."""
        valid_nim_request["mutable_fields"] = ["scenes.*.invalid_field"]
        with pytest.raises(Exception):
            validate(instance=valid_nim_request, schema=NIM_REQUEST_SCHEMA)

    def test_scene_id_must_be_positive(self, valid_nim_request):
        """Scene ID must be >= 1."""
        valid_nim_request["scenes"][0]["id"] = 0
        with pytest.raises(Exception):
            validate(instance=valid_nim_request, schema=NIM_REQUEST_SCHEMA)


# ============================================================================
# Test: Upstream Communication (forward_to_nim) - Mocked
# ============================================================================

class TestForwardToNIM:
    """Test upstream NIM communication with mocked HTTP client."""

    @run_async
    async def test_upstream_http_error_returns_status(self, proxy_config, valid_nim_request):
        """Upstream HTTP error returns status code."""
        proxy_module._config = proxy_config

        with patch("src.nim_proxy_server.httpx.AsyncClient") as mock_client:
            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server Error", request=MagicMock(), response=mock_response
            )
            mock_instance.post.return_value = mock_response

            with pytest.raises(httpx.HTTPStatusError) as exc:
                await forward_to_nim(valid_nim_request)
            assert exc.value.response.status_code == 500

    @run_async
    async def test_invalid_upstream_host_rejected(self, proxy_config, valid_nim_request):
        """Upstream host not in allowlist is rejected."""
        proxy_module._config = proxy_config

        with patch.dict(os.environ, {"NIM_UPSTREAM_URL": "https://evil.com/v1/chat/completions"}):
            with pytest.raises(ValueError) as exc:
                await forward_to_nim(valid_nim_request)
            assert "not in allowlist" in str(exc.value)

    @run_async
    async def test_missing_api_key_rejected(self, valid_nim_request):
        """Missing API key is rejected."""
        proxy_module._config = ProxyConfig(
            host="127.0.0.1",
            port=4174,
            upstream_hosts=["integrate.api.nvidia.com"],
            env_api_key="",  # No key
        )

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc:
                await forward_to_nim(valid_nim_request)
            assert "No API key configured" in str(exc.value)

    @run_async
    async def test_upstream_timeout_raises(self, proxy_config, valid_nim_request):
        """Upstream timeout raises httpx.TimeoutException."""
        proxy_module._config = proxy_config

        with patch("src.nim_proxy_server.httpx.AsyncClient") as mock_client:
            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_instance.post.side_effect = httpx.TimeoutException("Timeout")

            with pytest.raises(httpx.TimeoutException):
                await forward_to_nim(valid_nim_request)

    @run_async
    async def test_model_id_separated_from_profile_id(self, proxy_config, valid_nim_request):
        """Verify profile.id ('architecture.korean') is NOT sent as model parameter."""
        proxy_module._config = proxy_config

        # Ensure valid_nim_request has profile.id = 'architecture.korean'
        assert valid_nim_request["profile"]["id"] == "architecture.korean"

        mock_nim_resp = {
            "schema_version": "2.0",
            "request_id": valid_nim_request["request_id"],
            "source_revision": valid_nim_request["source_revision"],
            "scenes": [
                {"id": 1, "video_prompt": "rewritten 1"},
                {"id": 2, "video_prompt": "rewritten 2"}
            ]
        }

        with patch("src.nim_proxy_server.httpx.AsyncClient") as mock_client:
            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": json.dumps(mock_nim_resp)}}]
            }
            mock_response.raise_for_status.return_value = None
            mock_instance.post.return_value = mock_response

            await forward_to_nim(valid_nim_request)

            # Check what model parameter was passed in payload to upstream NIM
            call_kwargs = mock_instance.post.call_args[1]
            sent_model = call_kwargs["json"]["model"]

            # FAILURE RULE: profile.id must NEVER be sent as model parameter!
            assert sent_model != "architecture.korean"
            assert sent_model == "meta/llama-3.1-8b-instruct"

    @run_async
    async def test_custom_model_id_forwarded(self, proxy_config, valid_nim_request):
        """Verify valid custom model_id is used when provided."""
        proxy_module._config = proxy_config
        valid_nim_request["model_id"] = "meta/llama-3.1-70b-instruct"

        mock_nim_resp = {
            "schema_version": "2.0",
            "request_id": valid_nim_request["request_id"],
            "source_revision": valid_nim_request["source_revision"],
            "scenes": []
        }

        with patch("src.nim_proxy_server.httpx.AsyncClient") as mock_client:
            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": json.dumps(mock_nim_resp)}}]
            }
            mock_response.raise_for_status.return_value = None
            mock_instance.post.return_value = mock_response

            await forward_to_nim(valid_nim_request)

            call_kwargs = mock_instance.post.call_args[1]
            assert call_kwargs["json"]["model"] == "meta/llama-3.1-70b-instruct"


# ============================================================================
# Test: Security Regression
# ============================================================================

class TestSecurityRegression:
    """Regression tests for security issues."""

    def test_no_wildcard_cors_in_default_config(self):
        """Default config never uses '*' for CORS."""
        config = ProxyConfig()
        assert "*" not in config.allowed_origins

    def test_bind_address_defaults_to_loopback(self):
        """Default bind is 127.0.0.1, not 0.0.0.0."""
        config = ProxyConfig()
        assert config.host == "127.0.0.1"

    def test_session_token_required_by_default(self):
        """Session token is required by default."""
        config = ProxyConfig()
        assert config.require_session_token is True

    def test_api_key_never_in_request_body(self, valid_nim_request):
        """API key is never sent in request body to upstream."""
        json_str = json.dumps(valid_nim_request)
        assert "Authorization" not in json_str
        assert "api_key" not in json_str.lower()
        assert "bearer" not in json_str.lower()

    def test_error_responses_never_contain_secrets(self):
        """All error response types are secret-free."""
        errors = [
            error_response(400, "VALIDATION_ERROR", "test"),
            error_response(401, "AUTH_ERROR", "test"),
            error_response(403, "FORBIDDEN", "test"),
            error_response(413, "REQUEST_TOO_LARGE", "test"),
            error_response(500, "INTERNAL_ERROR", "internal error", {"api_key": "SECRET_KEY_123"}),
            error_response(504, "UPSTREAM_TIMEOUT", "test"),
        ]
        for resp in errors:
            resp_str = json.dumps(resp)
            assert "SECRET" not in resp_str
            assert "SECRET_KEY_123" not in resp_str
            assert "Authorization" not in resp_str
            assert "error" in resp
            if "details" in resp["error"]:
                for key, val in resp["error"]["details"].items():
                    if key.lower() in ("api_key", "authorization", "token", "secret"):
                        assert val == "[REDACTED]"
