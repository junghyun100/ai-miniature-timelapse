"""
WP-3 Response Post-Normalization & Scene Fallback Tests

Validates:
1. Response Parsing & Header Restoration (schema_version, request_id, source_revision, codeblock stripping).
2. Scene Canonicalization & Invariant Rules:
   - Scene 1 first-frame prompt presence & single master image.
   - Scene 2+ first-frame prompt removal (cleared if injected by NIM).
   - Identity Lock presence in all video_prompts and first_frame_prompts.
   - Negative Prompt re-inserted once-last (IMMUTABLE_NEGATIVE preserved unmutated).
3. Scene Fallback Generation & Reconciler:
   - Missing scene detection and deterministic fallback scene creation from local scene plans.
   - Provenance tracking (NIM, NIM_PARTIAL_FALLBACK, FALLBACK).
4. Lineage Resolver & Ancestor Chain:
   - Sequential lineage revision recomputation.
   - Preservation of parent ancestor lineage revision (changes upstream alter downstream lineage).
5. Field Order Normalization:
   - Canonical plan field ordering (Header -> MASTER IMAGE -> Scenes 1..N).
"""

import json

import pytest

from src.domain import (
    AssetKind,
    AssetRef,
    AssetScope,
    InputMode,
    Project,
    ProvenanceSource,
    Scene,
    ScenePlan,
    StyleBible,
    WorkflowMode,
)
from src.fallback_builder import create_fallback_scene, reconcile_scenes_with_fallback
from src.lineage_resolver import resolve_project_lineage
from src.response_normalizer import (
    normalize_field_order,
    normalize_nim_response,
    parse_raw_nim_response,
)
from src.scene_canonicalizer import canonicalize_scene
from src.serializers import IMMUTABLE_NEGATIVE


@pytest.fixture
def sample_style_bible() -> StyleBible:
    return StyleBible(
        identity_lock="A single coherent Korean hanok: one-story warm timber structure",
        materials={
            "primary": ["timber", "stone"],
            "secondary": ["giwa tiles"],
            "tools": ["chisel"],
        },
        camera={
            "lens": "85mm macro",
            "angle": "45-degree",
            "movement": "locked",
            "distance": "fixed",
        },
        lighting={
            "key": "warm daylight",
            "fill": "soft",
            "mood": "cinematic",
            "consistency": "locked",
        },
        color_palette=["warm wood", "charcoal-black roof tiles"],
        workspace="one compacted-earth miniature site",
        hands_rule="giant human hands only",
        motion_rule="rapid procedural timelapse",
    )


@pytest.fixture
def sample_project(sample_style_bible: StyleBible) -> Project:
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
        scene_plans=[
            ScenePlan(
                scene_id=1,
                name="Foundation and Walls",
                start_state="empty site",
                ordered_actions=["place footings", "raise columns"],
                end_state="wall frame complete",
                forbidden_changes=[],
                input_mode=InputMode.MASTER_IMAGE,
            ),
            ScenePlan(
                scene_id=2,
                name="Roofing and Exterior",
                start_state="wall frame",
                ordered_actions=["add rafters", "place tiles"],
                end_state="roof complete",
                forbidden_changes=[],
                input_mode=InputMode.PREVIOUS_FINAL_FRAME,
            ),
            ScenePlan(
                scene_id=3,
                name="Landscaping and Reveal",
                start_state="roof complete",
                ordered_actions=["add moss", "reveal hanok"],
                end_state="complete hanok",
                forbidden_changes=[],
                input_mode=InputMode.PREVIOUS_FINAL_FRAME,
            ),
        ],
        scene_count=3,
        source_revision="",
    )
    project.source_revision = project.compute_source_revision()

    # Initial scenes
    scene1 = create_fallback_scene(
        1, project.scene_plans[0], sample_style_bible, project.profile_id, topic=project.topic
    )
    scene2 = create_fallback_scene(
        2, project.scene_plans[1], sample_style_bible, project.profile_id, topic=project.topic
    )
    scene3 = create_fallback_scene(
        3, project.scene_plans[2], sample_style_bible, project.profile_id, topic=project.topic
    )

    project.scenes = resolve_project_lineage([scene1, scene2, scene3], project.source_revision)
    return project


# ============================================================================
# 1. Response Parse & Header Restoration Tests
# ============================================================================


class TestResponseParse:
    def test_parse_json_dict(self):
        data = {"request_id": "req123", "scenes": [{"id": 1, "video_prompt": "test"}]}
        parsed = parse_raw_nim_response(data, expected_request_id="req123")
        assert parsed["request_id"] == "req123"
        assert parsed["schema_version"] == "2.0"

    def test_parse_codeblock_markdown_wrapper(self):
        raw_str = """```json
        {
            "request_id": "req-block",
            "scenes": [{"id": 1, "video_prompt": "wrapped in codeblock"}]
        }
        ```"""
        parsed = parse_raw_nim_response(raw_str, expected_request_id="req-block")
        assert parsed["request_id"] == "req-block"
        assert len(parsed["scenes"]) == 1

    def test_parse_restores_missing_header_fields(self):
        raw_str = '{"scenes": [{"id": 1, "video_prompt": "no headers"}]}'
        parsed = parse_raw_nim_response(
            raw_str, expected_request_id="req-restore", expected_source_revision="sha256:abc"
        )
        assert parsed["request_id"] == "req-restore"
        assert parsed["source_revision"] == "sha256:abc"
        assert parsed["schema_version"] == "2.0"

    def test_parse_stale_request_id_raises_value_error(self):
        data = {"request_id": "req-old", "source_revision": "sha256:abc"}
        with pytest.raises(ValueError, match="Stale NIM response: request_id mismatch"):
            parse_raw_nim_response(data, expected_request_id="req-new")

    def test_parse_stale_source_revision_raises_value_error(self):
        data = {"request_id": "req-1", "source_revision": "sha256:old"}
        with pytest.raises(ValueError, match="Stale NIM response: source_revision mismatch"):
            parse_raw_nim_response(
                data, expected_request_id="req-1", expected_source_revision="sha256:new"
            )


# ============================================================================
# 2. Scene Canonicalization & Invariant Rules Tests
# ============================================================================


class TestSceneCanonicalizer:
    def test_scene1_first_frame_presence(self, sample_style_bible: StyleBible):
        scene = Scene(
            id=1,
            name="Scene 1",
            input_mode=InputMode.MASTER_IMAGE,
            asset_ref=AssetRef("master", AssetKind.IMAGE, AssetScope.PROJECT),
            first_frame_prompt="Initial master setup",
            video_prompt="Scene 1 action",
            template_exclusions="none",
            negative_prompt=IMMUTABLE_NEGATIVE,
            clip_duration_seconds=10,
            lineage_revision="",
        )
        canonical = canonicalize_scene(scene, 1, sample_style_bible.identity_lock)
        assert canonical.input_mode == InputMode.MASTER_IMAGE
        assert canonical.first_frame_prompt is not None
        assert sample_style_bible.identity_lock in canonical.first_frame_prompt

    def test_scene2_first_frame_cleared_if_injected(self, sample_style_bible: StyleBible):
        """Failure Rule: Scene 2+ first frame MUST NOT be regenerated or kept."""
        scene = Scene(
            id=2,
            name="Scene 2",
            input_mode=InputMode.PREVIOUS_FINAL_FRAME,
            asset_ref=AssetRef("s1_final", AssetKind.IMAGE, AssetScope.SCENE),
            first_frame_prompt="FORBIDDEN_SECOND_FRAME_PROMPT",  # NIM injected this!
            video_prompt="Scene 2 action",
            template_exclusions="none",
            negative_prompt=IMMUTABLE_NEGATIVE,
            clip_duration_seconds=10,
            lineage_revision="",
        )
        canonical = canonicalize_scene(scene, 2, sample_style_bible.identity_lock)
        assert canonical.input_mode == InputMode.PREVIOUS_FINAL_FRAME
        assert canonical.first_frame_prompt is None  # MUST be cleared!

    def test_identity_lock_enforced_in_video_prompt(self, sample_style_bible: StyleBible):
        scene = Scene(
            id=1,
            name="Scene 1",
            input_mode=InputMode.MASTER_IMAGE,
            asset_ref=AssetRef("master", AssetKind.IMAGE, AssetScope.PROJECT),
            first_frame_prompt="Setup",
            video_prompt="Build walls with fast motion.",  # Missing identity lock!
            template_exclusions="none",
            negative_prompt=IMMUTABLE_NEGATIVE,
            clip_duration_seconds=10,
            lineage_revision="",
        )
        canonical = canonicalize_scene(scene, 1, sample_style_bible.identity_lock)
        assert sample_style_bible.identity_lock in canonical.video_prompt

    def test_negative_line_unmutated_once_last(self, sample_style_bible: StyleBible):
        """Failure Rule: negative line MUST NOT be altered or mutated."""
        scene = Scene(
            id=1,
            name="Scene 1",
            input_mode=InputMode.MASTER_IMAGE,
            asset_ref=AssetRef("master", AssetKind.IMAGE, AssetScope.PROJECT),
            first_frame_prompt="Setup",
            video_prompt="Build walls.",
            template_exclusions="none",
            negative_prompt="ALTERED_BAD_NEGATIVE",  # NIM tried to alter it!
            clip_duration_seconds=10,
            lineage_revision="",
        )
        canonical = canonicalize_scene(scene, 1, sample_style_bible.identity_lock)
        assert canonical.negative_prompt == IMMUTABLE_NEGATIVE


# ============================================================================
# 3. Fallback Builder & Missing Scene Coverage Tests
# ============================================================================


class TestFallbackBuilder:
    def test_nim_result_keeps_english_override_without_reappending_korean(
        self, sample_project: Project
    ):
        korean_instruction = "피사체를 화면의 80%로 크게"
        sample_project.user_overrides = {
            "additional_instructions": korean_instruction,
            "scale": "subject occupies approximately 80% of the frame",
        }
        nim_data = [
            {
                "id": 1,
                "first_frame_prompt": f"Large subject filling 80% of frame. {korean_instruction}",
                "video_prompt": f"Preserve the large subject scale. {korean_instruction}",
            },
            {"id": 2, "video_prompt": "Preserve the large subject scale."},
            {"id": 3, "video_prompt": "Preserve the large subject scale."},
        ]

        scenes, fallbacks, prov_source = reconcile_scenes_with_fallback(nim_data, sample_project)

        assert fallbacks == []
        assert prov_source == ProvenanceSource.NIM
        assert korean_instruction not in scenes[0].first_frame_prompt
        assert korean_instruction not in scenes[0].video_prompt
        assert "Large subject filling 80% of frame" in scenes[0].first_frame_prompt
        assert "subject occupies approximately 80% of the frame" in scenes[0].video_prompt

    def test_missing_scene_2_triggers_partial_fallback(self, sample_project: Project):
        """NIM returns scenes 1 and 3, omitting scene 2."""
        nim_data = [
            {"id": 1, "first_frame_prompt": "ff 1", "video_prompt": "NIM scene 1 video prompt"},
            {"id": 3, "video_prompt": "NIM scene 3 video prompt"},
        ]

        scenes, fallbacks, prov_source = reconcile_scenes_with_fallback(nim_data, sample_project)

        assert len(scenes) == 3
        assert fallbacks == [2]
        assert prov_source == ProvenanceSource.NIM_PARTIAL_FALLBACK
        assert scenes[1].id == 2
        # Fallback scene 2 has identity lock and IMMUTABLE_NEGATIVE
        assert sample_project.style_bible.identity_lock in scenes[1].video_prompt
        assert scenes[1].negative_prompt == IMMUTABLE_NEGATIVE

    def test_all_scenes_missing_triggers_full_fallback(self, sample_project: Project):
        """NIM returns empty array."""
        scenes, fallbacks, prov_source = reconcile_scenes_with_fallback([], sample_project)

        assert len(scenes) == 3
        assert fallbacks == [1, 2, 3]
        assert prov_source == ProvenanceSource.FALLBACK

    def test_all_scenes_provided_returns_nim_provenance(self, sample_project: Project):
        """NIM returns scenes 1, 2, 3."""
        nim_data = [
            {"id": 1, "first_frame_prompt": "ff 1", "video_prompt": "NIM s1"},
            {"id": 2, "video_prompt": "NIM s2"},
            {"id": 3, "video_prompt": "NIM s3"},
        ]

        scenes, fallbacks, prov_source = reconcile_scenes_with_fallback(nim_data, sample_project)

        assert len(scenes) == 3
        assert fallbacks == []
        assert prov_source == ProvenanceSource.NIM


# ============================================================================
# 4. Lineage Resolver & Ancestor Chain Tests
# ============================================================================


class TestLineageResolver:
    def test_lineage_revision_incorporates_ancestor(self, sample_project: Project):
        """
        Failure Rule: lineage hash ancestor MUST NOT be missing.
        Verifies that Scene N's lineage_revision depends on Scene N-1's lineage_revision.
        """
        resolved = resolve_project_lineage(sample_project.scenes, sample_project.source_revision)
        s1_rev = resolved[0].lineage_revision
        s2_rev = resolved[1].lineage_revision
        s3_rev = resolved[2].lineage_revision

        assert s1_rev.startswith("sha256:")
        assert s2_rev.startswith("sha256:")
        assert s3_rev.startswith("sha256:")
        assert s1_rev != s2_rev != s3_rev

        # Change Scene 1's video prompt and re-resolve
        sample_project.scenes[0].video_prompt += " Mutated prompt"
        re_resolved = resolve_project_lineage(sample_project.scenes, sample_project.source_revision)

        new_s1_rev = re_resolved[0].lineage_revision
        new_s2_rev = re_resolved[1].lineage_revision
        new_s3_rev = re_resolved[2].lineage_revision

        # Scene 1 changed -> Scene 1 revision changes
        assert new_s1_rev != s1_rev
        # Ancestor changed -> Scene 2 and Scene 3 revisions MUST change!
        assert new_s2_rev != s2_rev
        assert new_s3_rev != s3_rev


# ============================================================================
# 5. Complete Post-Normalization Pipeline & Field Order Tests
# ============================================================================


class TestResponseNormalizerPipeline:
    def test_normalize_nim_response_end_to_end(self, sample_project: Project):
        """End-to-end post-normalization of raw NIM response string."""
        raw_nim_json = json.dumps(
            {
                "request_id": "req-e2e",
                "source_revision": sample_project.source_revision,
                "scenes": [
                    {"id": 1, "first_frame_prompt": "custom ff1", "video_prompt": "custom vid1"},
                    {"id": 3, "video_prompt": "custom vid3"},
                    # Scene 2 missing!
                ],
            }
        )

        updated_project, provenance = normalize_nim_response(
            raw_response=raw_nim_json,
            project=sample_project,
            model_id="meta/llama-3.1-8b-instruct",
            expected_request_id="req-e2e",
        )

        assert updated_project.scene_count == 3
        assert provenance.source == ProvenanceSource.NIM_PARTIAL_FALLBACK
        assert provenance.fallback_scene_ids == [2]

        # Verify Scene 1 first frame has identity lock
        assert (
            sample_project.style_bible.identity_lock in updated_project.scenes[0].first_frame_prompt
        )
        # Verify Scene 2+ first frame is None
        assert updated_project.scenes[1].first_frame_prompt is None
        assert updated_project.scenes[2].first_frame_prompt is None

        # Verify negative prompt on all scenes
        for s in updated_project.scenes:
            assert s.negative_prompt == IMMUTABLE_NEGATIVE

    def test_field_order_serialization(self, sample_project: Project):
        """Validates canonical plan field ordering."""
        serialized = normalize_field_order(sample_project)

        lines = serialized.split("\n")

        # 1. Project Header at top
        assert lines[0].startswith("Project:")
        assert any(line.startswith("Source Revision:") for line in lines[:10])

        # 2. MASTER IMAGE block
        assert "MASTER IMAGE" in serialized
        assert "First Frame Prompt:" in serialized

        # 3. SCENE blocks
        assert "SCENE 1 —" in serialized
        assert "SCENE 2 —" in serialized
        assert "SCENE 3 —" in serialized
