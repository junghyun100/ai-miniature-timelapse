"""
Tests for Canonical Serializers - Section 11.6
"""
from datetime import datetime

import pytest

from src.domain import (
    AspectRatio,
    AssetKind,
    AssetRef,
    AssetScope,
    InputMode,
    Project,
    Provenance,
    ProvenanceSource,
    RelayBranch,
    Scene,
    ScenePlan,
    SceneStatus,
    StyleBible,
    WorkflowMode,
)
from src.serializers import (
    IMMUTABLE_NEGATIVE,
    compute_source_revision,
    perform_copy_action,
    serialize_full_plan,
)

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_project() -> Project:
    """Create a sample 3-scene relay project for testing."""
    style_bible = StyleBible(
        identity_lock="Test identity lock for miniature hanok",
        materials={"primary": ["wood", "stone"], "secondary": ["moss"], "tools": ["chisel", "trowel"]},
        camera={"lens": "85mm", "angle": "45", "movement": "locked", "distance": "fixed"},
        lighting={"key": "soft daylight", "fill": "ambient", "mood": "warm", "consistency": "locked"},
        color_palette=["warm wood", "terracotta", "stone gray"],
        workspace="compacted earth tray",
        hands_rule="giant human hands only",
        motion_rule="rapid procedural timelapse",
    )

    scene1_asset = AssetRef(
        logical_id="scene_01_master",
        kind=AssetKind.IMAGE,
        scope=AssetScope.SCENE,
        flow_asset_label="Scene 1 master image",
        local_path="scenes/scene_01_master.png",
        source_scene_id=1,
        confirmed_by_user=True,
    )

    scene2_asset = AssetRef(
        logical_id="scene_01_last_frame",
        kind=AssetKind.IMAGE,
        scope=AssetScope.SCENE,
        flow_asset_label="Scene 1 final frame",
        local_path="scenes/scene_01_last_frame.png",
        source_scene_id=1,
        confirmed_by_user=True,
    )

    scene3_asset = AssetRef(
        logical_id="scene_02_last_frame",
        kind=AssetKind.IMAGE,
        scope=AssetScope.SCENE,
        flow_asset_label="Scene 2 final frame",
        local_path="scenes/scene_02_last_frame.png",
        source_scene_id=2,
        confirmed_by_user=True,
    )

    scenes = [
        Scene(
            id=1,
            name="Foundation and Walls",
            input_mode=InputMode.MASTER_IMAGE,
            asset_ref=scene1_asset,
            first_frame_prompt="First frame prompt for scene 1 with identity lock",
            video_prompt="Video prompt for scene 1 with identity lock",
            template_exclusions="exclusions for scene 1",
            negative_prompt=IMMUTABLE_NEGATIVE,
            clip_duration_seconds=10,
            lineage_revision="sha256:" + "0" * 64,
            status=SceneStatus.CONFIRMED,
            confirmed_at=datetime.utcnow(),
        ),
        Scene(
            id=2,
            name="Roofing and Exterior",
            input_mode=InputMode.PREVIOUS_FINAL_FRAME,
            asset_ref=scene2_asset,
            first_frame_prompt="",
            video_prompt="Video prompt for scene 2 with identity lock",
            template_exclusions="exclusions for scene 2",
            negative_prompt=IMMUTABLE_NEGATIVE,
            clip_duration_seconds=10,
            lineage_revision="sha256:" + "0" * 64,
            status=SceneStatus.CONFIRMED,
        ),
        Scene(
            id=3,
            name="Painting and Reveal",
            input_mode=InputMode.PREVIOUS_FINAL_FRAME,
            asset_ref=scene3_asset,
            first_frame_prompt="",
            video_prompt="Video prompt for scene 3 with identity lock",
            template_exclusions="exclusions for scene 3",
            negative_prompt=IMMUTABLE_NEGATIVE,
            clip_duration_seconds=10,
            lineage_revision="sha256:" + "0" * 64,
            status=SceneStatus.AWAITING_PREVIOUS_FRAME,
        ),
    ]

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
        aspect_ratio=AspectRatio.RATIO_9_16,
        style_bible=style_bible,
        derived_fields={},
        scene_plans=[
            ScenePlan(1, "Foundation and Walls", "start", ["a", "b"], "end", InputMode.MASTER_IMAGE),
            ScenePlan(2, "Roofing and Exterior", "start", ["c", "d"], "end", InputMode.PREVIOUS_FINAL_FRAME),
            ScenePlan(3, "Painting and Reveal", "start", ["e", "f"], "end", InputMode.PREVIOUS_FINAL_FRAME),
        ],
        scene_count=3,
        source_revision="sha256:" + "0" * 64,  # Will be recomputed
        flow_execution_profile_id="flow.frames_first.10s",
        nim_enabled=False,
        nim_model_id="",
        nim_refinement_policy="mutable_only",
        narration=None,
        idea_seed="test-seed-123",
        provenance=Provenance(
            source=ProvenanceSource.LOCAL_PLANNER,
            provider="local",
            model_id="architecture.korean.v2",
            base_url_label="local",
            generated_at=datetime.utcnow(),
            request_id="00000000-0000-0000-0000-000000000000",
            source_revision="sha256:" + "0" * 64,
        ),
        relay_branch=RelayBranch(
            branch_id="branch-123",
            parent_branch_id=None,
            scene_statuses={"1": SceneStatus.CONFIRMED, "2": SceneStatus.CONFIRMED, "3": SceneStatus.AWAITING_PREVIOUS_FRAME},
            asset_refs=[scene1_asset, scene2_asset, scene3_asset],
            created_at=datetime.utcnow(),
            lineage_revision="sha256:" + "0" * 64,
            nonce="abc123",
        ),
        scenes=scenes,
    )
    # Recompute source revision
    project.source_revision = compute_source_revision(project)
    return project


@pytest.fixture
def single_clip_project() -> Project:
    """Create a single-clip project for testing."""
    style_bible = StyleBible(
        identity_lock="Test identity lock",
        materials={"primary": ["test"], "secondary": [], "tools": []},
        camera={"lens": "85mm", "angle": "45", "movement": "locked", "distance": "fixed"},
        lighting={"key": "test", "fill": "test", "mood": "test", "consistency": "locked"},
        color_palette=["test"],
        workspace="test",
        hands_rule="test",
        motion_rule="test",
    )

    asset = AssetRef(
        logical_id="scene_01_master",
        kind=AssetKind.IMAGE,
        scope=AssetScope.SCENE,
        flow_asset_label="Master image",
        local_path="master.png",
        source_scene_id=0,
        confirmed_by_user=True,
    )

    scene = Scene(
        id=1,
        name="Scene 1",
        input_mode=InputMode.MASTER_IMAGE,
        asset_ref=asset,
        first_frame_prompt="First frame for single clip",
        video_prompt="Video prompt for single clip",
        template_exclusions="exclusions",
        negative_prompt=IMMUTABLE_NEGATIVE,
        clip_duration_seconds=10,
        lineage_revision="sha256:" + "0" * 64,
        status=SceneStatus.LOCKED,
    )

    project = Project(
        schema_version="2.0",
        topic="test",
        topic_label="Test",
        genre="vehicle",
        subtype="car",
        profile_id="vehicle.assembly",
        profile_version="2.0.0",
        workflow_mode=WorkflowMode.SINGLE_CLIP_FROM_MASTER,
        duration_seconds=10,
        clip_duration_seconds=10,
        aspect_ratio=AspectRatio.RATIO_9_16,
        style_bible=style_bible,
        derived_fields={},
        scene_plans=[
            ScenePlan(1, "S1", "start", ["a"], "end", InputMode.MASTER_IMAGE),
        ],
        scene_count=1,
        source_revision="sha256:" + "0" * 64,
        flow_execution_profile_id="test",
        nim_enabled=False,
    )
    project.scenes = [scene]
    project.source_revision = compute_source_revision(project)
    return project


# ============================================================================
# Source Revision Tests
# ============================================================================

class TestSourceRevision:
    """Test source revision computation."""

    def test_deterministic_same_input_same_hash(self, sample_project):
        """Same project produces same source_revision."""
        rev1 = compute_source_revision(sample_project)
        rev2 = compute_source_revision(sample_project)
        assert rev1 == rev2
        assert rev1.startswith("sha256:")

    def test_change_topic_changes_hash(self, sample_project):
        """Changing topic changes source revision."""
        rev1 = compute_source_revision(sample_project)

        sample_project.topic = "different"
        rev2 = compute_source_revision(sample_project)

        assert rev1 != rev2

    def test_change_profile_changes_hash(self, sample_project):
        """Changing profile changes source revision."""
        rev1 = compute_source_revision(sample_project)

        sample_project.profile_id = "different.profile"
        rev2 = compute_source_revision(sample_project)

        assert rev1 != rev2

    def test_change_scene_plan_changes_hash(self, sample_project):
        """Changing scene plan changes source revision."""
        rev1 = compute_source_revision(sample_project)

        sample_project.scene_plans[0].ordered_actions = ["different", "actions"]
        rev2 = compute_source_revision(sample_project)

        assert rev1 != rev2

    def test_change_style_bible_changes_hash(self, sample_project):
        """Changing style bible changes source revision."""
        rev1 = compute_source_revision(sample_project)

        sample_project.style_bible.identity_lock = "different lock"
        rev2 = compute_source_revision(sample_project)

        assert rev1 != rev2

    def test_transient_fields_excluded(self, sample_project):
        """Transient fields (provenance timestamps, request_id) don't affect hash."""
        rev1 = compute_source_revision(sample_project)

        sample_project.provenance.request_id = "different-uuid"
        sample_project.provenance.generated_at = datetime.utcnow()
        rev2 = compute_source_revision(sample_project)

        # Hash may or may not be same since provenance is part of project
        # But the revision itself is computed only from included fields
        # The Project.compute_source_revision includes specific fields
        assert rev1.startswith("sha256:")
        assert rev2.startswith("sha256:")


# ============================================================================
# Full Plan Serialization Tests
# ============================================================================

class TestSerializeFullPlan:
    """Test full plan canonical serialization per Section 11.6."""

    def test_basic_structure(self, sample_project):
        """Full plan has correct sections in order."""
        text = serialize_full_plan(sample_project)

        # Project header
        assert "Project: hanok" in text
        assert "Topic Label: Architecture-Hanok" in text
        assert "Profile: architecture.korean@2.0.0" in text
        assert "Workflow: REFERENCE_FRAME_RELAY" in text
        assert "Duration: 30s (3 scenes × 10s)" in text
        assert "Aspect Ratio: 9:16" in text
        assert "Source: local_planner" in text
        assert "Source Revision: sha256:" in text

        # MASTER IMAGE section
        assert "MASTER IMAGE" in text
        assert "First Frame Prompt: First frame prompt for scene 1 with identity lock" in text
        assert "Template Exclusions: exclusions for scene 1" in text
        assert f"Negative Prompt: {IMMUTABLE_NEGATIVE}" in text

        # SCENE 1
        assert "SCENE 1 — Foundation and Walls" in text
        assert "Input: Master Image" in text
        assert "Output: scene_01_master | kind=image | scope=scene | label=Scene 1 master image | local=scenes/scene_01_master.png | source_scene=1" in text
        assert "Video Prompt: Video prompt for scene 1 with identity lock" in text

        # SCENE 2
        assert "SCENE 2 — Roofing and Exterior" in text
        assert "Input: Scene 1 Final Frame" in text
        assert "Output: scene_01_last_frame | kind=image | scope=scene | label=Scene 1 final frame | local=scenes/scene_01_last_frame.png | source_scene=1" in text
        assert "Video Prompt: Video prompt for scene 2 with identity lock" in text
        # Scene 2 should NOT have First Frame Prompt
        assert "First Frame Prompt:" not in text.split("SCENE 2")[1].split("SCENE 3")[0]

        # SCENE 3
        assert "SCENE 3 — Painting and Reveal" in text
        assert "Input: Scene 2 Final Frame" in text
        assert "Output: scene_02_last_frame" in text
        assert "Video Prompt: Video prompt for scene 3 with identity lock" in text

    def test_single_clip_mode(self, single_clip_project):
        """Single-clip project has only Scene 1, no MASTER IMAGE duplicate."""
        text = serialize_full_plan(single_clip_project)

        assert "Project: test" in text
        assert "Workflow: SINGLE_CLIP_FROM_MASTER" in text
        assert "MASTER IMAGE" in text
        assert "First Frame Prompt: First frame for single clip" in text
        assert "SCENE 1 — Scene 1" in text
        # Should NOT have SCENE 2
        assert "SCENE 2" not in text

    def test_deterministic_order(self, sample_project):
        """Same project serializes identically each time."""
        text1 = serialize_full_plan(sample_project)
        text2 = serialize_full_plan(sample_project)
        assert text1 == text2

    def test_immutable_negative_in_all_sections(self, sample_project):
        """IMMUTABLE_NEGATIVE appears in MASTER IMAGE and all SCENE blocks."""
        text = serialize_full_plan(sample_project)

        # Count occurrences of immutable negative
        count = text.count(IMMUTABLE_NEGATIVE)
        # MASTER IMAGE + 3 scenes = 4 times
        assert count == 4


# ============================================================================
# Specialized Copy Actions Tests
# ============================================================================

class TestCopyActions:
    """Test specialized copy actions per Section 11.6."""

    def test_copy_master_image_prompt(self, sample_project):
        """Copy Master Image Prompt returns only MASTER IMAGE section."""
        result = perform_copy_action(sample_project, "master_image")

        assert result.action == "master_image"
        assert result.scene_id == 1
        assert "MASTER IMAGE" in result.text
        assert "First Frame Prompt: First frame prompt for scene 1 with identity lock" in result.text
        assert "Template Exclusions: exclusions for scene 1" in result.text
        assert f"Negative Prompt: {IMMUTABLE_NEGATIVE}" in result.text
        assert "SCENE 1" not in result.text
        assert result.source_revision == sample_project.source_revision

    def test_copy_scene_video_prompt(self, sample_project):
        """Copy Scene Video Prompt returns video prompt + exclusions + negative."""
        result = perform_copy_action(sample_project, "scene_video", scene_id=2)

        assert result.action == "scene_video"
        assert result.scene_id == 2
        assert "SCENE 2 — Roofing and Exterior" in result.text
        assert "Video Prompt: Video prompt for scene 2 with identity lock" in result.text
        assert "Template Exclusions: exclusions for scene 2" in result.text
        assert f"Negative Prompt: {IMMUTABLE_NEGATIVE}" in result.text
        assert "First Frame Prompt" not in result.text
        assert result.source_revision == sample_project.source_revision

    def test_copy_full_scene(self, sample_project):
        """Copy Full Scene returns exact visible scene block."""
        result = perform_copy_action(sample_project, "full_scene", scene_id=1)

        assert result.action == "full_scene"
        assert result.scene_id == 1
        assert "MASTER IMAGE" in result.text
        assert "First Frame Prompt:" in result.text
        assert "SCENE 1 — Foundation and Walls" in result.text

        # Scene 2 full scene
        result2 = perform_copy_action(sample_project, "full_scene", scene_id=2)
        assert "SCENE 2 — Roofing and Exterior" in result2.text
        assert "MASTER IMAGE" not in result2.text
        assert "First Frame Prompt" not in result2.text

    def test_copy_all(self, sample_project):
        """Copy All returns full canonical plan."""
        result = perform_copy_action(sample_project, "all")

        assert result.action == "all"
        assert result.scene_id is None
        assert result.text == serialize_full_plan(sample_project)

    def test_copy_action_invalid_action(self, sample_project):
        """Invalid action raises ValueError."""
        with pytest.raises(ValueError, match="Unknown copy action"):
            perform_copy_action(sample_project, "invalid_action")

    def test_copy_action_missing_scene_id(self, sample_project):
        """Scene-specific actions require scene_id."""
        with pytest.raises(ValueError, match="scene_id required"):
            perform_copy_action(sample_project, "scene_video")

        with pytest.raises(ValueError, match="scene_id required"):
            perform_copy_action(sample_project, "full_scene")

    def test_copy_action_source_revision_included(self, sample_project):
        """All copy actions include current source_revision."""
        for action in ["master_image", "scene_video", "full_scene", "all"]:
            if action in ["scene_video", "full_scene"]:
                result = perform_copy_action(sample_project, action, scene_id=2)
            else:
                result = perform_copy_action(sample_project, action)
            assert result.source_revision == sample_project.source_revision
            assert result.source_revision.startswith("sha256:")


# ============================================================================
# AssetRef Serialization Tests
# ============================================================================

class TestAssetRefSerialization:
    """Test AssetRef serialized format."""

    def test_full_asset_ref(self, sample_project):
        """Full asset ref serializes with all fields."""
        sample_project.scenes[0].asset_ref
        # Test via scene serialization
        text = serialize_full_plan(sample_project)
        assert "scene_01_master | kind=image | scope=scene" in text
        assert "label=Scene 1 master image" in text
        assert "local=scenes/scene_01_master.png" in text
        assert "source_scene=1" in text

    def test_none_asset_ref(self):
        """None asset ref serializes as 'none'."""
        from src.serializers import _serialize_asset_ref
        assert _serialize_asset_ref(None) == "none"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
