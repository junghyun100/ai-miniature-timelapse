"""
WP-2 UI Request Adapter Integration & Contract Tests

Validates:
- Monotonic Request IDs
- Timeout & Abort Controller handling
- Retry policy (exponential backoff, 429/5xx retry, 400/401/403/404 immediate fail)
- Stale Guard protection (request_id & source_revision match validation)
- Loading state transitions (IDLE, LOADING, RETRYING, SUCCESS, ERROR, ABORTED, STALE)
- Failure rules (no post-timeout apply, no abort-as-success, no stale overwrite)
- Provenance model without secrets
"""

from unittest.mock import AsyncMock

import pytest

from src.domain import compute_source_revision
from src.error_handling import (
    HttpError,
    RequestAbortedError,
    RequestTimeoutError,
    StaleResponseError,
    is_retryable_error,
    is_retryable_status,
    sanitize_error_message,
)
from src.fetch_wrapper import FetchWrapper
from src.provenance_model import ProvenanceModel, ProvenanceSource
from src.state_store import RequestState, StateStore
from src.ui_adapter import UIRequestAdapter

# ============================================================================
# 1. Monotonic Request ID Tests
# ============================================================================


def test_monotonic_request_id_generation():
    """Verify request ID is strictly monotonically increasing."""
    adapter = UIRequestAdapter()
    id1 = adapter.get_next_request_id()
    id2 = adapter.get_next_request_id()
    id3 = adapter.get_next_request_id()

    assert id1 == 1
    assert id2 == 2
    assert id3 == 3
    assert id1 < id2 < id3


# ============================================================================
# 2. Provenance Model Tests
# ============================================================================


def test_provenance_model_creation_and_dict():
    """Verify ProvenanceModel serializes clean dict without secrets."""
    prov = ProvenanceModel(
        source=ProvenanceSource.NIM,
        provider="nvidia_nim",
        model_id="meta/llama-3.1-8b-instruct",
        base_url_label="NVIDIA Integrate API",
        request_id=42,
        source_revision="sha256:abc12345",
        fallback_scene_ids=[2],
        validation_warnings=["Warning: fallback used"],
    )

    d = prov.to_dict()
    assert d["source"] == "nim"
    assert d["provider"] == "nvidia_nim"
    assert d["model_id"] == "meta/llama-3.1-8b-instruct"
    assert d["base_url_label"] == "NVIDIA Integrate API"
    assert d["request_id"] == 42
    assert d["source_revision"] == "sha256:abc12345"
    assert d["fallback_scene_ids"] == [2]
    assert d["validation_warnings"] == ["Warning: fallback used"]
    assert "api_key" not in d
    assert "secret" not in d


def test_provenance_local_fallback():
    """Verify local provenance factory."""
    local_prov = ProvenanceModel.create_local(request_id=5, source_revision="sha256:def")
    assert local_prov.source == ProvenanceSource.LOCAL
    assert local_prov.provider == "local_deterministic"
    assert local_prov.request_id == 5


# ============================================================================
# 3. Error Handling & Sanitization Tests
# ============================================================================


def test_error_sanitization():
    """Verify API keys and tokens are redacted from error messages."""
    raw_msg = "Failed request with nvapi-123456789abcdef and key='secret_token_123'"
    sanitized = sanitize_error_message(raw_msg)
    assert "nvapi-" not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized
    assert "[REDACTED_SECRET]" in sanitized


def test_is_retryable_classification():
    """Verify retryable vs non-retryable HTTP status codes."""
    assert is_retryable_status(429) is True
    assert is_retryable_status(500) is True
    assert is_retryable_status(503) is True

    assert is_retryable_status(400) is False
    assert is_retryable_status(401) is False
    assert is_retryable_status(403) is False
    assert is_retryable_status(404) is False

    assert is_retryable_error(RequestTimeoutError("timeout")) is False
    assert is_retryable_error(RequestAbortedError("aborted")) is False
    assert is_retryable_error(StaleResponseError("stale")) is False


# ============================================================================
# 4. State Store & Stale Guard Tests
# ============================================================================


def test_state_store_stale_guard_rejection():
    """Verify Stale Guard rejects responses with mismatched request_id or source_revision."""
    store = StateStore()
    store.start_request(request_id=10, source_revision="sha256:v1")

    # Mismatched request_id
    res1 = store.accept_plan(
        request_id=9,
        source_revision="sha256:v1",
        plan={"scenes": []},
        provenance=ProvenanceModel.create_local(9, "sha256:v1"),
    )
    assert res1["accepted"] is False
    assert store.state == RequestState.STALE
    assert store.applied_plan is None  # Must NOT overwrite plan!

    # Reset for second check
    store.start_request(request_id=11, source_revision="sha256:v2")

    # Mismatched source_revision
    res2 = store.accept_plan(
        request_id=11,
        source_revision="sha256:v1_old",
        plan={"scenes": []},
        provenance=ProvenanceModel.create_local(11, "sha256:v1_old"),
    )
    assert res2["accepted"] is False
    assert store.state == RequestState.STALE
    assert store.applied_plan is None  # Must NOT overwrite plan!


def test_state_store_valid_acceptance():
    """Verify Stale Guard accepts valid matching response."""
    store = StateStore()
    store.start_request(request_id=12, source_revision="sha256:v3")

    plan_data = {"scenes": [{"id": 1, "video_prompt": "test"}]}
    prov = ProvenanceModel(source=ProvenanceSource.NIM, request_id=12, source_revision="sha256:v3")

    res = store.accept_plan(
        request_id=12,
        source_revision="sha256:v3",
        plan=plan_data,
        provenance=prov,
    )

    assert res["accepted"] is True
    assert store.state == RequestState.SUCCESS
    assert store.applied_plan == plan_data
    assert store.provenance == prov


def test_state_store_failure_rules():
    """Verify failure rules: Abort is NOT success, Timeout sets ERROR state."""
    store = StateStore()

    # Abort test
    store.start_request(request_id=15, source_revision="sha256:v4")
    store.fail_request(15, RequestAbortedError("User cancelled", request_id=15))

    assert store.state == RequestState.ABORTED
    assert store.state != RequestState.SUCCESS
    assert store.applied_plan is None

    # Timeout test
    store.start_request(request_id=16, source_revision="sha256:v5")
    store.fail_request(
        16, RequestTimeoutError("Client timeout of 60s exceeded", timeout_seconds=60.0)
    )

    assert store.state == RequestState.ERROR
    assert store.state != RequestState.SUCCESS
    assert store.applied_plan is None


# ============================================================================
# 5. UI Request Adapter Async Execution & Retry Tests
# ============================================================================


@pytest.mark.anyio
async def test_ui_adapter_successful_flow():
    """Test full successful request lifecycle through UIRequestAdapter."""
    draft = {"topic": "Hanok"}
    expected_rev = compute_source_revision(draft)

    mock_fetch = AsyncMock()
    mock_fetch.return_value = {
        "request_id": 1,
        "source_revision": expected_rev,
        "scenes": [{"id": 1, "video_prompt": "NIM refined prompt"}],
        "provenance": {"source": "nim"},
    }

    fetch_wrapper = FetchWrapper()
    fetch_wrapper.fetch_json = mock_fetch

    adapter = UIRequestAdapter(fetch_wrapper=fetch_wrapper)

    result = await adapter.execute_request(
        url="https://fake-endpoint.com/v1",
        payload={"topic": "Hanok"},
        draft=draft,
    )

    assert result["success"] is True
    assert result["state"] == RequestState.SUCCESS
    assert adapter.get_loading_state() == RequestState.SUCCESS
    assert adapter.get_applied_plan() == mock_fetch.return_value
    assert adapter.get_provenance().source == ProvenanceSource.NIM


@pytest.mark.anyio
async def test_ui_adapter_retry_on_429_then_success():
    """Test automatic retries on 429 rate limit error followed by success."""
    call_count = 0

    async def mock_single_attempt(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise HttpError("Rate limited", status_code=429)
        json_data = kwargs.get("json_data") or {}
        return {
            "request_id": json_data.get("request_id"),
            "source_revision": json_data.get("source_revision"),
            "scenes": [],
        }

    fetch_wrapper = FetchWrapper(backoff_base=0.01)
    fetch_wrapper._single_attempt = AsyncMock(side_effect=mock_single_attempt)

    adapter = UIRequestAdapter(fetch_wrapper=fetch_wrapper)
    draft = {"topic": "Vehicle"}

    result = await adapter.execute_request(
        url="https://fake-endpoint.com/v1",
        payload={},
        draft=draft,
    )

    assert result["success"] is True
    assert call_count == 2
    assert result["state"] == RequestState.SUCCESS


@pytest.mark.anyio
async def test_ui_adapter_non_retryable_401_immediate_failure():
    """Test 401 Unauthorized fails immediately without retry."""
    fetch_wrapper = FetchWrapper(backoff_base=0.01)
    fetch_wrapper.fetch_json = AsyncMock(side_effect=HttpError("Unauthorized", status_code=401))

    adapter = UIRequestAdapter(fetch_wrapper=fetch_wrapper)
    draft = {"topic": "Cooking"}

    result = await adapter.execute_request(
        url="https://fake-endpoint.com/v1",
        payload={},
        draft=draft,
    )

    assert result["success"] is False
    assert result["state"] == RequestState.ERROR
    assert "Unauthorized" in result["error"]


@pytest.mark.anyio
async def test_ui_adapter_timeout_handling():
    """Test client timeout cancels request and enforces Failure Rule: timeout response not applied."""
    fetch_wrapper = FetchWrapper()
    fetch_wrapper.fetch_json = AsyncMock(
        side_effect=RequestTimeoutError("60s timeout exceeded", timeout_seconds=60.0)
    )

    adapter = UIRequestAdapter(fetch_wrapper=fetch_wrapper)
    draft = {"topic": "Product"}

    result = await adapter.execute_request(
        url="https://fake-endpoint.com/v1",
        payload={},
        draft=draft,
    )

    assert result["success"] is False
    assert result["state"] == RequestState.ERROR
    assert adapter.get_applied_plan() is None  # Timeout response NOT applied!


@pytest.mark.anyio
async def test_ui_adapter_abort_in_flight_on_new_request():
    """Test starting a new request automatically aborts the previous active in-flight request."""
    adapter = UIRequestAdapter()

    # Start request 1 in state store
    req_id_1 = adapter.get_next_request_id()
    adapter.state_store.start_request(req_id_1, "sha256:v1")
    assert adapter.state_store.is_busy() is True

    # Draft change triggers cancel of request 1
    adapter.on_draft_change({"topic": "Hanok edited"})

    assert adapter.state_store.state == RequestState.ABORTED
    assert adapter.state_store.applied_plan is None  # Abort NOT treated as success!
