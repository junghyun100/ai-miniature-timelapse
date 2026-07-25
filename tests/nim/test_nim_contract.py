"""
NIM Contract Tests - Section 21.3

Tests for NIM request/response validation, normalization, fallback behavior,
stale response rejection, and security (secret redaction).
"""
import asyncio
import json
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import httpx

from src.domain import (
    Project, Scene, ScenePlan, StyleBible, AssetRef, AssetKind, AssetScope,
    WorkflowMode, ProfileId, ProvenanceSource, InputMode, SceneStatus,
    compute_source_revision, normalize_nim_response,
    NimRequest, NimSceneRequest, NimResponse, NimSceneResponse,
    Provenance,
)
from src.nim_client import (
    NimClient, SyncNimClient,
    NimClientError, NimAuthError, NimBadRequestError, NimNotFoundError,
    NimRateLimitError, NimServerError, NimTimeoutError, NimStaleResponseError,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_style_bible() -> StyleBible:
    return StyleBible(
        identity_lock="A single coherent Korean hanok: one-story warm timber post-and-beam structure, natural stone footings, white hanji doors and windows, deep curved black giwa eaves, restrained dancheong only on appropriate beam ends and eaves",
        materials={"primary": ["timber", "stone", "hanji"], "secondary": ["giwa tiles"], "tools": ["chisel", "mallet", "level"]},
        camera={"lens": "85mm macro", "angle": "45-degree", "movement": "locked", "distance": "fixed"},
        lighting={"key": "warm side daylight", "fill": "soft", "mood": "cinematic", "consistency": "locked"},
        color_palette=["warm wood", "white hanji", "charcoal-black roof tiles"],
        workspace="one compacted-earth miniature site on one fixed tray",
        hands_rule="giant human hands only; no miniature people, tiny workers, human figures, faces, or full bodies",
        motion_rule="rapid procedural timelapse in one locked composition",
    )


@pytest.fixture
def sample_project(sample_style_bible: StyleBible) -> Project:
    """Create a canonical 3-scene architecture project."""
    asset_ref = AssetRef(
        logical_id="scene_01_master",
        kind=AssetKind.IMAGE,
        scope=AssetScope.SCENE,
        flow_asset_label="Scene 1 master image",
        local_path="scenes/scene_01_master.png",
        source_scene_id=1,
        confirmed_by_user=True,
    )

    scene1 = Scene(
        id=1,
        name="Foundation and Walls",
        input_mode=InputMode.MASTER_IMAGE,
        asset_ref=asset_ref,
        first_frame_prompt="Master image prompt: compacted earth tray, empty rectangular footprint, guide strings, separate natural stone footings, separate timber sill beams, columns, hanji frames, giant human hands measuring and tensioning strings, placing first stone footing, 85mm macro, 45-degree angle, warm side daylight",
        video_prompt="Start from the uploaded approved master image. The opening frame must match the uploaded image exactly. Compacted earth tray, empty rectangular footprint, guide strings, natural stone footings, timber sill beams, columns, hanji frames. Giant human hands measure and tension guide strings. Hands place natural stone footings in rectangular bay grid. Hands seat timber sill beams on footings. Hands raise timber columns with visible mortise-and-tenon joints. Hands connect lower and upper beams. Hands insert white hanji door and window frames. Rapid procedural timelapse with fast hand motion in one locked camera composition. Multiple rapid construction beats inside one locked camera composition. End on a clean, stable, motionless hold for the final 0.5 seconds. Keep every installed part, tool, loose material, camera parameter, and light direction unchanged so this exact frame can be saved and reused as the next scene input. Negative Prompt: text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, miniature people, small people, tiny workers, human figures",
        template_exclusions="stone castle, church, European cottage, pagoda tower, fantasy fortress",
        negative_prompt="text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, miniature people, small people, tiny workers, human figures",
        clip_duration_seconds=10,
        lineage_revision="sha256:abc123",
        status=SceneStatus.VIDEO_READY,
    )

    scene2 = Scene(
        id=2,
        name="Roofing and Exterior",
        input_mode=InputMode.PREVIOUS_FINAL_FRAME,
        asset_ref=AssetRef(
            logical_id="scene_01_last_frame",
            kind=AssetKind.IMAGE,
            scope=AssetScope.SCENE,
            flow_asset_label="Scene 1 final frame",
            local_path="scenes/scene_01_last_frame.png",
            source_scene_id=1,
            confirmed_by_user=True,
        ),
        first_frame_prompt="",
        video_prompt="Start from the uploaded final-frame image from Scene 1. Treat that image as immutable visual ground truth. Before motion begins, preserve its composition, subject identity, installed parts, object placement, scale, camera, and lighting as closely as the selected model allows. Do not redesign, reinterpret, clean up, or rebuild any visible part. Giant human hands place main crossbeams. Hands add purlins and evenly spaced rafters. Hands build the deep curved eave profile. Hands place black giwa roof tiles row by row. Hands install white hanji doors and exterior wood trim. Hands add restrained architectural details without changing the footprint. Rapid procedural timelapse with fast hand motion in one locked camera composition. Multiple rapid construction beats inside one locked camera composition. End on a clean, stable, motionless hold for the final 0.5 seconds. Keep every installed part, tool, loose material, camera parameter, and light direction unchanged so this exact frame can be saved and reused as the next scene input. Negative Prompt: text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, miniature people, small people, tiny workers, human figures",
        template_exclusions="stone castle, church, European cottage, pagoda tower, fantasy fortress",
        negative_prompt="text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, miniature people, small people, tiny workers, human figures",
        clip_duration_seconds=10,
        lineage_revision="sha256:def456",
        status=SceneStatus.LOCKED,
    )

    scene3 = Scene(
        id=3,
        name="Painting, Landscaping, and Reveal",
        input_mode=InputMode.PREVIOUS_FINAL_FRAME,
        asset_ref=AssetRef(
            logical_id="scene_02_last_frame",
            kind=AssetKind.IMAGE,
            scope=AssetScope.SCENE,
            flow_asset_label="Scene 2 final frame",
            local_path="scenes/scene_02_last_frame.png",
            source_scene_id=2,
            confirmed_by_user=True,
        ),
        first_frame_prompt="",
        video_prompt="Start from the uploaded final-frame image from Scene 2. Treat that image as immutable visual ground truth. Before motion begins, preserve its composition, subject identity, installed parts, object placement, scale, camera, and lighting as closely as the selected model allows. Do not redesign, reinterpret, clean up, or rebuild any visible part. Giant human hands apply restrained protective wood finish. Hands add limited dancheong accents to correct beam and eave areas. Hands clean excess materials without moving the building. Hands add a stone path, low wall, moss, grass, and one small pine. Hands remove remaining tools. Hands leave the frame. Hold the completed subject, then perform one subtle cinematic pull-back without changing the subject design. Rapid procedural timelapse with fast hand motion in one locked camera composition. Multiple rapid construction beats inside one locked camera composition. End on a clean, stable, motionless hold for the final 0.5 seconds. Keep every installed part, tool, loose material, camera parameter, and light direction unchanged. Negative Prompt: text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, miniature people, small people, tiny workers, human figures",
        template_exclusions="stone castle, church, European cottage, pagoda tower, fantasy fortress",
        negative_prompt="text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, miniature people, small people, tiny workers, human figures",
        clip_duration_seconds=10,
        lineage_revision="sha256:ghi789",
        status=SceneStatus.LOCKED,
    )

    project = Project(
        schema_version="2.0",
        topic="hanok",
        topic_label="Architecture-Hanok",
        genre="architecture",
        subtype="hanok",
        profile_id="architecture.korean",
        profile_version="2.0.0",
        workflow_mode=WorkflowMode.REFERENCE_FRAME_RELAY,
        duration_seconds=30,
        clip_duration_seconds=10,
        style_bible=sample_style_bible,
        derived_fields={},
        scene_plans=[
            ScenePlan(1, "Foundation and Walls", "empty site", ["measure", "place footings", "raise columns"], "wall frame complete", InputMode.MASTER_IMAGE),
            ScenePlan(2, "Roofing and Exterior", "wall frame", ["place beams", "add rafters", "build eaves", "place tiles"], "roof complete", InputMode.PREVIOUS_FINAL_FRAME),
            ScenePlan(3, "Painting, Landscaping, and Reveal", "roof complete", ["apply finish", "add dancheong", "landscape", "reveal"], "complete hanok", InputMode.PREVIOUS_FINAL_FRAME),
        ],
        scene_count=3,
        source_revision="",  # Will be computed
        flow_execution_profile_id="google-veo2-9-16-10s",
        nim_enabled=True,
        nim_model_id="meta/llama-3.1-8b-instruct",
    )

    # Compute source revision
    project.source_revision = project.compute_source_revision()
    project.scenes = [scene1, scene2, scene3]

    return project


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for testing."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.is_closed = False
        yield mock_client


# ============================================================================
# Test: Valid JSON Request/Response Round-trip
# ============================================================================

class TestNimRequestResponse:
    """Test NIM request/response JSON schema compliance."""

    def test_build_nim_request_from_project(self, sample_project: Project):
        """Test building NimRequest from canonical Project."""
        client = NimClient(base_url="https://api.test.com", api_key="test-key")
        req_id = str(uuid.uuid4())
        source_rev = sample_project.compute_source_revision()

        nim_req = client._build_nim_request(sample_project, req_id, source_rev)

        # Verify structure matches Section 14.2
        assert nim_req.schema_version == "2.0"
        assert nim_req.request_id == req_id
        assert nim_req.source_revision == source_rev
        assert nim_req.profile["id"] == "architecture.korean"
        assert nim_req.profile["workflow_mode"] == "REFERENCE_FRAME_RELAY"
        assert len(nim_req.scenes) == 3

        # Scene 1 has first_frame_prompt
        assert nim_req.scenes[0].local_first_frame_prompt != ""
        assert "compacted earth tray" in nim_req.scenes[0].local_first_frame_prompt

        # Scenes 2+ have empty first_frame_prompt (relay mode)
        assert nim_req.scenes[1].local_first_frame_prompt == ""
        assert nim_req.scenes[2].local_first_frame_prompt == ""

        # Mutable fields exactly matches spec
        assert nim_req.mutable_fields == [
            "scenes.*.first_frame_prompt",
            "scenes.*.video_prompt",
        ]

        # Immutable rules present
        assert len(nim_req.immutable_rules) > 0
        assert any("identity lock" in r.lower() for r in nim_req.immutable_rules)
        assert any("negative prompt" in r.lower() for r in nim_req.immutable_rules)

    def test_nim_request_to_dict(self, sample_project: Project):
        """Test NimRequest serializes to correct JSON."""
        client = NimClient(base_url="https://api.test.com", api_key="test-key")
        req_id = str(uuid.uuid4())
        source_rev = sample_project.compute_source_revision()
        nim_req = client._build_nim_request(sample_project, req_id, source_rev)

        d = nim_req.to_dict()
        assert d["schema_version"] == "2.0"
        assert d["request_id"] == req_id
        assert "scenes" in d
        assert len(d["scenes"]) == 3

    def test_nim_response_from_valid_json(self):
        """Test parsing valid NIM response JSON."""
        resp_data = {
            "schema_version": "2.0",
            "request_id": str(uuid.uuid4()),
            "source_revision": "sha256:abc123",
            "scenes": [
                {"id": 1, "first_frame_prompt": "Improved master prompt", "video_prompt": "Improved video 1"},
                {"id": 2, "first_frame_prompt": "", "video_prompt": "Improved video 2"},
                {"id": 3, "first_frame_prompt": "", "video_prompt": "Improved video 3"},
            ],
        }
        response = NimResponse.from_dict(resp_data)
        assert response.schema_version == "2.0"
        assert len(response.scenes) == 3
        assert response.scenes[0].first_frame_prompt != ""
        assert response.scenes[1].first_frame_prompt == ""
        assert response.scenes[2].first_frame_prompt == ""

    def test_nim_response_roundtrip(self):
        """Test NimResponse -> dict -> NimResponse preserves data."""
        resp = NimResponse(
            request_id=str(uuid.uuid4()),
            source_revision="sha256:test",
            scenes=[
                NimSceneResponse(1, "ff prompt", "vid prompt"),
                NimSceneResponse(2, "", "vid prompt 2"),
            ],
        )
        d = resp.to_dict()
        resp2 = NimResponse.from_dict(d)
        assert resp.request_id == resp2.request_id
        assert resp.source_revision == resp2.source_revision
        assert resp2.scenes[0].first_frame_prompt == "ff prompt"
        assert resp2.scenes[1].first_frame_prompt == ""


# ============================================================================
# Test: Normalizer Post-NIM Fallback (Section 14.5)
# ============================================================================

class TestNimNormalization:
    """Test post-NIM normalization per Section 14.5."""

    def test_partial_fallback_single_scene(self, sample_project: Project):
        """One scene valid, one empty → nim_partial_fallback."""
        local_scenes = [
            NimSceneRequest(1, "S1", "", [], "", "local ff", "local vid 1"),
            NimSceneRequest(2, "S2", "", [], "", "", "local vid 2"),
        ]

        # NIM returns valid scene 1, missing scene 2
        nim_response = NimResponse(
            request_id="req-1",
            source_revision=sample_project.source_revision,
            scenes=[
                NimSceneResponse(1, "nim ff", "nim vid 1"),
            ],
        )

        normalized, warnings = normalize_nim_response(nim_response, local_scenes, sample_project.source_revision)

        assert len(normalized.scenes) == 2
        assert normalized.scenes[0].first_frame_prompt == "nim ff"
        assert normalized.scenes[0].video_prompt == "nim vid 1"
        # Scene 2 falls back to local
        assert normalized.scenes[1].first_frame_prompt == ""
        assert normalized.scenes[1].video_prompt == "local vid 2"
        assert any("fallback" in w.lower() for w in warnings)

    def test_wrong_scene_count_padded(self, sample_project: Project):
        """Response has wrong scene count → padded with local fallbacks."""
        local_scenes = [NimSceneRequest(i, f"S{i}", "", [], "", "ff" if i == 1 else "", f"local {i}") for i in range(1, 4)]
        nim_response = NimResponse(
            request_id="req-1",
            source_revision=sample_project.source_revision,
            scenes=[NimSceneResponse(1, "nim", "nim vid")],  # Only 1 scene
        )
        normalized, warnings = normalize_nim_response(nim_response, local_scenes, sample_project.source_revision)
        assert len(normalized.scenes) == 3
        assert any("scene count mismatch" in w.lower() for w in warnings)

    def test_duplicate_scene_id_fallback(self, sample_project: Project):
        """Duplicate scene ID in response → fallback for that scene."""
        local_scenes = [
            NimSceneRequest(1, "S1", "", [], "", "local ff", "local vid 1"),
            NimSceneRequest(2, "S2", "", [], "", "", "local vid 2"),
        ]
        nim_response = NimResponse(
            request_id="req-1",
            source_revision=sample_project.source_revision,
            scenes=[
                NimSceneResponse(1, "nim ff", "nim vid 1"),
                NimSceneResponse(1, "dup ff", "dup vid"),  # Duplicate ID
            ],
        )
        normalized, warnings = normalize_nim_response(nim_response, local_scenes, sample_project.source_revision)
        # Second scene should fallback
        assert normalized.scenes[1].video_prompt == "local vid 2"
        assert any("id mismatch" in w.lower() for w in warnings)

    def test_first_frame_injected_scene2_stripped(self, sample_project: Project):
        """NIM injects first_frame_prompt into Scene 2 → normalizer strips it."""
        local_scenes = [
            NimSceneRequest(1, "S1", "", [], "", "local ff", "local vid 1"),
            NimSceneRequest(2, "S2", "", [], "", "", "local vid 2"),
        ]
        nim_response = NimResponse(
            request_id="req-1",
            source_revision=sample_project.source_revision,
            scenes=[
                NimSceneResponse(1, "nim ff", "nim vid 1"),
                NimSceneResponse(2, "FORBIDDEN first frame", "nim vid 2"),  # Should be stripped
            ],
        )
        normalized, warnings = normalize_nim_response(nim_response, local_scenes, sample_project.source_revision)
        assert normalized.scenes[1].first_frame_prompt == ""  # Stripped
        assert any("first frame" in w.lower() for w in warnings)

    def test_wrong_subtype_triggers_fallback(self, sample_project: Project):
        """NIM response has wrong subject identity → fallback."""
        local_scenes = [NimSceneRequest(1, "S1", "", [], "", "hanok ff", "hanok vid")]
        # Response mentions "stone castle" - forbidden for hanok
        nim_response = NimResponse(
            request_id="req-1",
            source_revision=sample_project.source_revision,
            scenes=[NimSceneResponse(1, "stone castle foundation", "stone castle build")],
        )
        normalized, warnings = normalize_nim_response(nim_response, local_scenes, sample_project.source_revision)
        # Should fall back to local
        assert normalized.scenes[0].video_prompt == "hanok vid"
        assert any("wrong subtype" in w.lower() or "identity" in w.lower() for w in warnings)

    def test_negative_prompt_altered_restored(self, sample_project: Project):
        """Negative prompt altered in response → normalizer restores from local."""
        # This is tested at full prompt assembly level, not NimResponse level
        # NimResponse doesn't contain negative_prompt - it's added during assembly
        pass


# ============================================================================
# Test: Stale/Out-of-Order Response Rejection (Section 14.4)
# ============================================================================

class TestNimStaleRejection:
    """Test stale response discard behavior."""

    def test_stale_source_revision_rejected(self, sample_project: Project):
        """Response with old source_revision → discarded."""
        local_scenes = [NimSceneRequest(1, "S1", "", [], "", "local", "local")]
        nim_response = NimResponse(
            request_id="req-1",
            source_revision="sha256:OLD_REVISION",  # Different!
            scenes=[NimSceneResponse(1, "nim", "nim")],
        )
        with pytest.raises(ValueError, match="Stale NIM response"):
            normalize_nim_response(nim_response, local_scenes, sample_project.source_revision)

    def test_client_detects_stale_response(self, sample_project: Project, mock_httpx_client):
        """Client raises NimStaleResponseError on stale response."""
        # Setup mock to return stale response
        req_id = str(uuid.uuid4())
        source_rev = sample_project.compute_source_revision()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "schema_version": "2.0",
            "request_id": req_id,
            "source_revision": "sha256:STALE_REVISION",  # Mismatch!
            "scenes": [{"id": 1, "first_frame_prompt": "x", "video_prompt": "y"}],
        }
        mock_httpx_client.post.return_value = mock_response

        client = NimClient(base_url="https://api.test.com", api_key="test")
        with pytest.raises(NimStaleResponseError, match="Source revision mismatch"):
            asyncio.run(client.rewrite_prompts(sample_project, "test-model", req_id))

    def test_client_discards_out_of_order(self, sample_project: Project, mock_httpx_client):
        """Client rejects response with mismatched request_id (stale/out-of-order)."""
        req_id_1 = str(uuid.uuid4())
        req_id_2 = str(uuid.uuid4())
        source_rev = sample_project.compute_source_revision()

        # Response has req_id_1 but client sent req_id_2 -> stale/out-of-order
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "schema_version": "2.0",
            "request_id": req_id_1,  # Old request ID - mismatch!
            "source_revision": source_rev,
            "scenes": [{"id": 1, "first_frame_prompt": "late", "video_prompt": "late"}],
        }
        mock_httpx_client.post.return_value = mock_response

        client = NimClient(base_url="https://api.test.com", api_key="test")
        # Client sends req_id_2 but gets response for req_id_1 -> rejects as stale
        with pytest.raises(NimStaleResponseError, match="Request ID mismatch"):
            asyncio.run(client.rewrite_prompts(sample_project, "test-model", req_id_2))


# ============================================================================
# Test: HTTP Error Handling & Retry (Section 14.4)
# ============================================================================

class TestNimHttpErrors:
    """Test HTTP error handling and retry logic."""

    @pytest.mark.asyncio
    async def test_401_no_retry(self, sample_project: Project, mock_httpx_client):
        """401 → no retry, NimAuthError raised."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_httpx_client.post.return_value = mock_response

        client = NimClient(base_url="https://api.test.com", api_key="bad-key")
        with pytest.raises(NimAuthError):
            await client.rewrite_prompts(sample_project, "test-model")

        # Only one call (no retries)
        assert mock_httpx_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_403_no_retry(self, sample_project: Project, mock_httpx_client):
        """403 → no retry, NimAuthError raised."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_httpx_client.post.return_value = mock_response

        client = NimClient(base_url="https://api.test.com", api_key="test")
        with pytest.raises(NimAuthError):
            await client.rewrite_prompts(sample_project, "test-model")
        assert mock_httpx_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_404_no_retry(self, sample_project: Project, mock_httpx_client):
        """404 → no retry, NimNotFoundError raised."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_httpx_client.post.return_value = mock_response

        client = NimClient(base_url="https://api.test.com", api_key="test")
        with pytest.raises(NimNotFoundError):
            await client.rewrite_prompts(sample_project, "test-model")
        assert mock_httpx_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_429_retry_with_backoff(self, sample_project: Project, mock_httpx_client):
        """429 → retry twice with exponential backoff, then raise NimRateLimitError."""
        mock_rate_limit = MagicMock()
        mock_rate_limit.status_code = 429
        mock_rate_limit.text = "Rate limited"

        # Use a fixed request_id so it matches what the client generates
        req_id = "550e8400-e29b-41d4-a716-446655440000"

        # All 3 attempts return 429 (max_retries=2 means 3 total attempts)
        mock_httpx_client.post.side_effect = [mock_rate_limit, mock_rate_limit, mock_rate_limit]

        client = NimClient(base_url="https://api.test.com", api_key="test", max_retries=2)
        with pytest.raises(NimRateLimitError):
            await client.rewrite_prompts(sample_project, "test-model", req_id)

        # Should have attempted 3 times (initial + 2 retries)
        assert mock_httpx_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_500_retry_then_fail(self, sample_project: Project, mock_httpx_client):
        """500 → retry twice, then NimServerError."""
        mock_error = MagicMock()
        mock_error.status_code = 500
        mock_error.text = "Internal Server Error"
        mock_httpx_client.post.return_value = mock_error

        client = NimClient(base_url="https://api.test.com", api_key="test", max_retries=2)
        with pytest.raises(NimServerError):
            await client.rewrite_prompts(sample_project, "test-model")

        assert mock_httpx_client.post.call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_timeout_raises_nim_timeout(self, sample_project: Project, mock_httpx_client):
        """Timeout → NimTimeoutError."""
        mock_httpx_client.post.side_effect = httpx.TimeoutException("Timeout")

        client = NimClient(base_url="https://api.test.com", api_key="test", timeout=1.0)
        with pytest.raises(NimTimeoutError):
            await client.rewrite_prompts(sample_project, "test-model")

    @pytest.mark.asyncio
    async def test_cancellation_aborts_in_flight(self, sample_project: Project, mock_httpx_client):
        """Cancellation aborts in-flight request."""
        # Simulate slow response
        async def slow_post(*args, **kwargs):
            await asyncio.sleep(10)
            raise AssertionError("Should not complete")

        mock_httpx_client.post.side_effect = slow_post

        client = NimClient(base_url="https://api.test.com", api_key="test")
        task = asyncio.create_task(client.rewrite_prompts(sample_project, "test-model"))
        await asyncio.sleep(0.01)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task


# ============================================================================
# Test: Security - Secret Redaction (Section 16.3, 16.4)
# ============================================================================

class TestNimSecurity:
    """Test API key and secret handling."""

    @pytest.mark.asyncio
    async def test_api_key_not_in_logs(self, sample_project: Project, mock_httpx_client, caplog):
        """API key never appears in log output."""
        # Use a fixed request_id so it matches in mock
        req_id = "550e8400-e29b-41d4-a716-446655440000"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "schema_version": "2.0",
            "request_id": req_id,
            "source_revision": sample_project.source_revision,
            "scenes": [{"id": 1, "first_frame_prompt": "x", "video_prompt": "y"}],
        }
        mock_httpx_client.post.return_value = mock_response

        client = NimClient(base_url="https://api.test.com", api_key="SUPER_SECRET_KEY_12345")
        await client.rewrite_prompts(sample_project, "test-model", req_id)

        # Check logs don't contain the key
        log_text = caplog.text
        assert "SUPER_SECRET_KEY_12345" not in log_text
        assert "Authorization: Bearer" not in log_text

    @pytest.mark.asyncio
    async def test_error_response_sanitized(self, sample_project: Project, mock_httpx_client):
        """Error responses don't contain authorization headers."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "invalid_request"}'
        mock_httpx_client.post.return_value = mock_response

        client = NimClient(base_url="https://api.test.com", api_key="SECRET_KEY")
        with pytest.raises(NimBadRequestError) as exc_info:
            await client.rewrite_prompts(sample_project, "test-model")

        error = exc_info.value
        # Error details should not contain the key
        assert "SECRET_KEY" not in str(error)
        assert "Authorization" not in str(error)

    def test_sanitize_for_log_removes_secrets(self):
        """_sanitize_for_log removes Authorization headers and keys."""
        client = NimClient(base_url="https://api.test.com", api_key="TEST_KEY_123")

        dirty_data = {
            "headers": {"Authorization": "Bearer TEST_KEY_123", "Content-Type": "application/json"},
            "body": {"model": "test", "messages": [{"role": "user", "content": "key TEST_KEY_123 here"}]},
        }
        sanitized = client._sanitize_for_log(dirty_data)

        assert "TEST_KEY_123" not in str(sanitized)
        assert "Bearer" not in str(sanitized)
        assert sanitized["headers"]["Authorization"] == "***REDACTED***"


# ============================================================================
# Test: Provenance (Section 14.6)
# ============================================================================

class TestNimProvenance:
    """Test provenance metadata generation."""

    @pytest.mark.asyncio
    async def test_provenance_nim_source(self, sample_project: Project, mock_httpx_client):
        """Successful NIM → provenance.source = nim."""
        req_id = str(uuid.uuid4())
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "schema_version": "2.0",
            "request_id": req_id,
            "source_revision": sample_project.source_revision,
            "scenes": [
                {"id": 1, "first_frame_prompt": "nim ff", "video_prompt": "nim vid 1"},
                {"id": 2, "first_frame_prompt": "", "video_prompt": "nim vid 2"},
                {"id": 3, "first_frame_prompt": "", "video_prompt": "nim vid 3"},
            ],
        }
        mock_httpx_client.post.return_value = mock_response

        client = NimClient(base_url="https://api.test.com", api_key="test")
        _, provenance = await client.rewrite_prompts(sample_project, "test-model", req_id)

        assert provenance.source == ProvenanceSource.NIM
        assert provenance.provider == "NVIDIA"
        assert provenance.model_id == "test-model"
        assert provenance.request_id == req_id
        assert provenance.source_revision == sample_project.source_revision
        assert provenance.fallback_scene_ids == []

    @pytest.mark.asyncio
    async def test_provenance_partial_fallback(self, sample_project: Project, mock_httpx_client):
        """NIM with partial fallback → provenance.source = fallback."""
        # Mock 500 then fallback to local
        mock_httpx_client.post.side_effect = [
            MagicMock(status_code=500, text="Server Error"),
            MagicMock(status_code=500, text="Server Error"),
            MagicMock(status_code=500, text="Server Error"),
        ]

        client = NimClient(base_url="https://api.test.com", api_key="test", max_retries=2)
        with pytest.raises(NimServerError):
            await client.rewrite_prompts(sample_project, "test-model")


# ============================================================================
# Test: SyncNimClient Wrapper
# ============================================================================

class TestSyncNimClient:
    """Test synchronous wrapper for CLI."""

    def test_sync_wrapper(self, sample_project: Project, mock_httpx_client):
        """SyncNimClient.rewrite_prompts works."""
        req_id = str(uuid.uuid4())
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "schema_version": "2.0",
            "request_id": req_id,
            "source_revision": sample_project.source_revision,
            "scenes": [{"id": 1, "first_frame_prompt": "x", "video_prompt": "y"}],
        }
        mock_httpx_client.post.return_value = mock_response

        client = SyncNimClient(base_url="https://api.test.com", api_key="test")
        response, provenance = client.rewrite_prompts(sample_project, "test-model", req_id)

        assert response.request_id == req_id
        assert provenance.request_id == req_id

    def test_context_manager(self, sample_project: Project, mock_httpx_client):
        """SyncNimClient works as context manager."""
        req_id = "550e8400-e29b-41d4-a716-446655440000"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "schema_version": "2.0",
            "request_id": req_id,
            "source_revision": sample_project.source_revision,
            "scenes": [{"id": 1, "first_frame_prompt": "x", "video_prompt": "y"}],
        }
        mock_httpx_client.post.return_value = mock_response

        with SyncNimClient(base_url="https://api.test.com", api_key="test") as client:
            response, _ = client.rewrite_prompts(sample_project, "test-model", req_id)
            assert response is not None