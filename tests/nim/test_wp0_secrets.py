"""
WP-0 Security Tests: Browser-Stored Secret Removal & Key Rotation

Validates:
1. Raw API keys never exist in browser storage, export JSON, clipboard, logs, or errors.
2. Ephemeral session-scoped API key transmission and key rotation via proxy server.
3. Input masking and non-sensitive descriptive placeholders.
4. Redaction across backend error responses, HTTP headers, and serializers.
"""

import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.nim_proxy_server as proxy_module
from src.nim_client import NimClient
from src.nim_proxy_server import (
    ProxyConfig,
    _sanitize_headers,
    error_response,
    forward_to_nim,
    redact_text,
)
from src.serializers import perform_copy_action


class TestSecretRedaction:
    """Test string & object redaction for API keys and tokens."""

    def test_redact_text_patterns(self):
        sample_key = "nvapi-abc1234567"
        sample_bearer = "Bearer nvapi-shortkey1"

        assert redact_text(sample_key) == "[REDACTED]"
        assert redact_text(sample_bearer) == "Bearer [REDACTED]"
        assert redact_text('api_key="secret123"') == "[REDACTED]"

    def test_error_response_sanitization(self):
        secret = "secret123"
        resp = error_response(
            status=500,
            code="FAIL",
            message=f'Connection failed using api_key="{secret}"',
            details={"api_key": secret, "raw_error": f"Unauthorized Bearer {secret}"}
        )

        err = resp["error"]
        assert "[REDACTED]" in err["message"]
        assert err["details"]["api_key"] == "[REDACTED]"
        assert secret not in err["details"]["raw_error"]

    def test_serializer_copy_action_redaction(self, sample_project):
        sample_project.scenes[0].first_frame_prompt = "Master image prompt with nvapi-abc1234567 inside"
        res = perform_copy_action(sample_project, "master_image")
        assert "nvapi-abc1234567" not in res.text
        assert "[REDACTED]" in res.text

    def test_nim_client_log_sanitization(self):
        client = NimClient(base_url="https://api.test.com", api_key="nvapi-abc1234567")
        log_str = client._sanitize_for_log("Connecting with Bearer nvapi-abc1234567")
        assert "nvapi-abc1234567" not in log_str
        assert "***REDACTED***" in log_str


class TestSessionKeyTransmissionAndRotation:
    """Test session-scoped key delivery and key rotation in proxy server."""

    @pytest.fixture(autouse=True)
    def setup_proxy_config(self):
        proxy_module._config = ProxyConfig(
            allowed_origins=["http://127.0.0.1:4173"],
            upstream_hosts=["integrate.api.nvidia.com", "api.nvidia.com"],
        )

    @pytest.mark.anyio
    async def test_session_key_forwarding(self):
        session_key = "nvapi-shortkey3"
        payload = {
            "request_id": "req-1",
            "source_revision": "rev-1",
            "profile": {"id": "test"},
            "scenes": []
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_resp = AsyncMock()
            mock_resp.raise_for_status = AsyncMock()
            mock_resp.json = MagicMock(return_value={
                "choices": [{
                    "message": {
                        "content": '{"schema_version": "1.0", "request_id": "req-1", "source_revision": "rev-1", "scenes": []}'
                    }
                }]
            })
            mock_post.return_value = mock_resp

            await forward_to_nim(payload, session_api_key=session_key)

            # Verify session key passed in Authorization header
            headers = mock_post.call_args.kwargs.get("headers", {})
            assert headers.get("Authorization") == f"Bearer {session_key}"

    @pytest.mark.anyio
    async def test_key_rotation(self):
        """Verify rotating key from Key A to Key B updates upstream call."""
        payload = {
            "request_id": "req-1",
            "source_revision": "rev-1",
            "scenes": []
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_resp = AsyncMock()
            mock_resp.raise_for_status = AsyncMock()
            mock_resp.json = MagicMock(return_value={
                "choices": [{
                    "message": {
                        "content": '{"schema_version": "1.0", "request_id": "req-1", "source_revision": "rev-1", "scenes": []}'
                    }
                }]
            })
            mock_post.return_value = mock_resp

            # Request 1 with Key A
            await forward_to_nim(payload, session_api_key="nvapi-key-a1")
            assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer nvapi-key-a1"

            # Request 2 rotated to Key B
            await forward_to_nim(payload, session_api_key="nvapi-key-b2")
            assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer nvapi-key-b2"

    def test_sanitize_headers_includes_session_api_key(self):
        headers = [
            (b"x-nim-api-key", b"nvapi-shortkey4"),
            (b"x-api-key", b"secret-123"),
            (b"content-type", b"application/json"),
        ]
        sanitized = _sanitize_headers(headers)
        assert sanitized["x-nim-api-key"] == "[REDACTED]"
        assert sanitized["x-api-key"] == "[REDACTED]"
        assert sanitized["content-type"] == "application/json"


class TestFrontendSecretContract:
    """Test frontend code invariants for secret handling."""

    def test_ui_index_html_contracts(self):
        with open("ui/index.html", encoding="utf-8") as f:
            html = f.read()

        legacy_key_fragment = "miniature_timelapse_nim_" + "api_key"

        # Invariant 1: No localStorage.setItem for nim_api_key
        assert f"localStorage.setItem('{legacy_key_fragment}'" not in html

        # Invariant 2: Legacy stored key is purged on load
        assert "miniature_timelapse_nim_" in html
        assert "'api_key'" in html
        assert "localStorage.removeItem(legacyNimKeyStorageId)" in html

        # Invariant 3: browser accepts only proxy session token, not NVIDIA API key
        assert 'placeholder="Proxy session token (세션 전용, 브라우저 미저장)"' in html
        assert "Proxy Session Token" in html
        assert "NIM/NGC API 키" not in html

        # Invariant 4: No real-looking API key patterns in placeholder
        assert not re.search(r'placeholder=["\'][^"\']*nvapi-[^"\']*["\']', html)

        # Invariant 5: export JSON uses redactObjectSecrets
        assert "redactObjectSecrets" in html

    def test_ui_app_js_contracts(self):
        with open("ui/app.js", encoding="utf-8") as f:
            app_js = f.read()

        # Invariant: saveProjectState and loadProjectState use redactObjectSecrets
        assert "export function redactSecrets" in app_js
        assert "export function redactObjectSecrets" in app_js
        assert "redactObjectSecrets" in app_js
