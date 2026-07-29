"""
Tests for Persistence Layer - Section 16.2
"""
import json
import tempfile
from datetime import datetime
from pathlib import Path

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
from src.persistence import (
    CURRENT_SCHEMA_VERSION,
    _get_project_state_path,
    _get_storage_dir,
    _quarantine_file,
    delete_project_state,
    get_active_scene_index,
    get_supported_schema_versions,
    is_project_resumable,
    list_projects,
    load_project_state,
    save_project_state,
)

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_base_dir():
    """Create a temporary base directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_project() -> Project:
    """Create a sample project for testing."""
    style_bible = StyleBible(
        identity_lock="Test identity lock for miniature hanok",
        materials={
            "primary": ["wood", "stone"],
            "secondary": ["moss"],
            "tools": ["chisel", "trowel"],
        },
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
            first_frame_prompt="First frame prompt for scene 1",
            video_prompt="Video prompt for scene 1 with identity lock",
            template_exclusions="exclusions",
            negative_prompt="negative prompt text",
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
            template_exclusions="exclusions",
            negative_prompt="negative prompt text",
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
            template_exclusions="exclusions",
            negative_prompt="negative prompt text",
            clip_duration_seconds=10,
            lineage_revision="sha256:" + "0" * 64,
            status=SceneStatus.AWAITING_PREVIOUS_FRAME,
        ),
    ]

    return Project(
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
        source_revision="sha256:" + "0" * 64,
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


# ============================================================================
# Save/Load Tests
# ============================================================================

class TestSaveLoad:
    """Test saving and loading project state."""

    def test_save_new_project(self, temp_base_dir, sample_project):
        """Save a new project (no project_id provided)."""
        result = save_project_state(temp_base_dir, sample_project)

        assert result.success
        assert result.project is not None

        project_id = result.project_id
        assert project_id is not None
        assert len(project_id) == 8  # uuid4[:8]

        # Verify file exists
        state_path = _get_project_state_path(temp_base_dir, project_id)
        assert state_path.exists()

    def test_save_load_roundtrip(self, temp_base_dir, sample_project):
        """Save and load a project, verify data integrity."""
        # Save
        save_result = save_project_state(temp_base_dir, sample_project)
        assert save_result.success
        project_id = save_result.project_id

        # Load
        load_result = load_project_state(temp_base_dir, project_id)
        assert load_result.success
        loaded_project = load_result.project

        # Verify key fields match
        assert loaded_project.topic == sample_project.topic
        assert loaded_project.topic_label == sample_project.topic_label
        assert loaded_project.profile_id == sample_project.profile_id
        assert loaded_project.workflow_mode == sample_project.workflow_mode
        assert loaded_project.duration_seconds == sample_project.duration_seconds
        assert loaded_project.source_revision == sample_project.source_revision
        assert loaded_project.idea_seed == sample_project.idea_seed

        # Verify scenes
        assert len(loaded_project.scenes) == len(sample_project.scenes)
        for orig, loaded in zip(sample_project.scenes, loaded_project.scenes, strict=False):
            assert loaded.id == orig.id
            assert loaded.name == orig.name
            assert loaded.input_mode == orig.input_mode
            assert loaded.first_frame_prompt == orig.first_frame_prompt
            assert loaded.video_prompt == orig.video_prompt
            assert loaded.status == orig.status

        # Verify relay branch
        assert loaded_project.relay_branch is not None
        assert sample_project.relay_branch is not None
        assert loaded_project.relay_branch.branch_id == sample_project.relay_branch.branch_id
        assert loaded_project.relay_branch.scene_statuses == sample_project.relay_branch.scene_statuses

    def test_save_with_existing_project_id(self, temp_base_dir, sample_project):
        """Save with a specific project_id."""
        custom_id = "my-custom-id"
        result = save_project_state(temp_base_dir, sample_project, project_id=custom_id)

        assert result.success
        assert result.project_id == custom_id

    def test_save_preserves_schema_version(self, temp_base_dir, sample_project):
        """Saved state includes current schema version."""
        save_project_state(temp_base_dir, sample_project, project_id="test-id")

        state_path = _get_project_state_path(temp_base_dir, "test-id")
        with open(state_path) as f:
            data = json.load(f)

        assert data["schema_version"] == CURRENT_SCHEMA_VERSION

    def test_save_includes_timestamp(self, temp_base_dir, sample_project):
        """Saved state includes last_saved_at timestamp."""
        save_project_state(temp_base_dir, sample_project, project_id="test-id")

        state_path = _get_project_state_path(temp_base_dir, "test-id")
        with open(state_path) as f:
            data = json.load(f)

        assert "last_saved_at" in data
        assert data["last_saved_at"].endswith("Z")


# ============================================================================
# Load Error Handling Tests
# ============================================================================

class TestLoadErrors:
    """Test error handling when loading project state."""

    def test_load_nonexistent_project(self, temp_base_dir):
        """Load non-existent project returns error."""
        result = load_project_state(temp_base_dir, "nonexistent")
        assert not result.success
        assert "not found" in result.error.lower()

    def test_load_corrupted_json(self, temp_base_dir):
        """Load corrupted JSON quarantines file."""
        # Create corrupted file
        project_id = "corrupt-test"
        storage_dir = _get_storage_dir(temp_base_dir, project_id)
        storage_dir.mkdir(parents=True, exist_ok=True)
        state_path = _get_project_state_path(temp_base_dir, project_id)
        state_path.write_text("{ invalid json }")

        result = load_project_state(temp_base_dir, project_id)
        assert not result.success
        assert result.quarantined
        assert "json" in result.error.lower()

        # Original file should be moved to quarantine
        assert not state_path.exists()

    def test_load_invalid_schema_version(self, temp_base_dir, sample_project):
        """Load project with wrong major schema version quarantines it."""
        # Save valid project first
        save_project_state(temp_base_dir, sample_project, project_id="schema-test")

        # Modify schema version in file
        state_path = _get_project_state_path(temp_base_dir, "schema-test")
        with open(state_path) as f:
            data = json.load(f)
        data["schema_version"] = "1.0"  # Different major version
        with open(state_path, "w") as f:
            json.dump(data, f)

        result = load_project_state(temp_base_dir, "schema-test")
        assert not result.success
        assert result.quarantined

    def test_load_missing_required_fields(self, temp_base_dir):
        """Load project with missing required fields quarantines it."""
        project_id = "missing-fields"
        storage_dir = _get_storage_dir(temp_base_dir, project_id)
        storage_dir.mkdir(parents=True, exist_ok=True)
        state_path = _get_project_state_path(temp_base_dir, project_id)

        # Write incomplete data
        state_path.write_text(json.dumps({"topic": "test"}))

        result = load_project_state(temp_base_dir, project_id)
        assert not result.success
        assert result.quarantined


# ============================================================================
# Delete Tests
# ============================================================================

class TestDelete:
    """Test deleting project state."""

    def test_delete_existing_project(self, temp_base_dir, sample_project):
        """Delete an existing project."""
        save_result = save_project_state(temp_base_dir, sample_project, project_id="to-delete")
        assert save_result.success

        delete_result = delete_project_state(temp_base_dir, "to-delete")
        assert delete_result.success

        # Verify gone
        load_result = load_project_state(temp_base_dir, "to-delete")
        assert not load_result.success

    def test_delete_nonexistent_project(self, temp_base_dir):
        """Delete non-existent project returns error."""
        result = delete_project_state(temp_base_dir, "nonexistent")
        assert not result.success
        assert "not found" in result.error.lower()


# ============================================================================
# List Projects Tests
# ============================================================================

class TestListProjects:
    """Test listing saved projects."""

    def test_list_empty_directory(self, temp_base_dir):
        """List projects in empty directory returns empty list."""
        projects = list_projects(temp_base_dir)
        assert projects == []

    def test_list_single_project(self, temp_base_dir, sample_project):
        """List returns one project with metadata."""
        save_project_state(temp_base_dir, sample_project, project_id="proj-1")

        projects = list_projects(temp_base_dir)
        assert len(projects) == 1
        assert projects[0]["project_id"] == "proj-1"
        assert projects[0]["topic"] == "hanok"
        assert projects[0]["profile_id"] == "architecture.korean"

    def test_list_multiple_projects_sorted_by_time(self, temp_base_dir, sample_project):
        """List returns projects sorted by last_saved_at descending."""
        # Save first project
        save_project_state(temp_base_dir, sample_project, project_id="proj-a")

        # Small delay to ensure different timestamps
        import time
        time.sleep(0.01)

        # Save second project
        save_project_state(temp_base_dir, sample_project, project_id="proj-b")

        projects = list_projects(temp_base_dir)
        assert len(projects) == 2
        # proj-b should be first (most recent)
        assert projects[0]["project_id"] == "proj-b"
        assert projects[1]["project_id"] == "proj-a"

    def test_list_ignores_invalid_entries(self, temp_base_dir, sample_project):
        """List ignores directories without valid state file."""
        save_project_state(temp_base_dir, sample_project, project_id="valid-proj")

        # Create invalid entry (directory without state file)
        invalid_dir = temp_base_dir / "invalid-proj"
        invalid_dir.mkdir()

        projects = list_projects(temp_base_dir)
        assert len(projects) == 1
        assert projects[0]["project_id"] == "valid-proj"


# ============================================================================
# Active Scene Index Tests
# ============================================================================

class TestActiveSceneIndex:
    """Test determining active scene from relay state."""

    def test_no_relay_branch(self, sample_project):
        """No relay branch returns 0."""
        sample_project.relay_branch = None
        assert get_active_scene_index(sample_project) == 0

    def test_first_incomplete_scene(self, sample_project):
        """Returns index of first non-COMPLETE scene."""
        # Scene 1 = CONFIRMED, Scene 2 = CONFIRMED, Scene 3 = AWAITING_PREVIOUS_FRAME
        assert get_active_scene_index(sample_project) == 2  # 0-based index (scene 3)

    def test_all_complete(self, sample_project):
        """All scenes COMPLETE returns last scene index."""
        # Mark all complete
        for scene in sample_project.scenes:
            sample_project.relay_branch.scene_statuses[str(scene.id)] = SceneStatus.COMPLETE
        assert get_active_scene_index(sample_project) == 2  # Last scene (index 2)

    def test_empty_project(self, sample_project):
        """Empty scenes returns 0."""
        sample_project.scenes = []
        sample_project.relay_branch.scene_statuses = {}
        assert get_active_scene_index(sample_project) == 0


# ============================================================================
# Resumable Check Tests
# ============================================================================

class TestResumable:
    """Test project resumable check."""

    def test_complete_project_is_resumable(self, sample_project):
        """Project with scenes and source_revision is resumable."""
        assert is_project_resumable(sample_project)

    def test_no_scenes_not_resumable(self, sample_project):
        """Project with no scenes is not resumable."""
        sample_project.scenes = []
        assert not is_project_resumable(sample_project)

    def test_no_source_revision_not_resumable(self, sample_project):
        """Project without source_revision is not resumable."""
        sample_project.source_revision = ""
        assert not is_project_resumable(sample_project)

    def test_no_profile_id_not_resumable(self, sample_project):
        """Project without profile_id is not resumable."""
        sample_project.profile_id = ""
        assert not is_project_resumable(sample_project)


# ============================================================================
# Storage Path Tests
# ============================================================================

class TestStoragePaths:
    """Test storage path utilities."""

    def test_get_storage_dir(self):
        """Storage dir format is correct."""
        base = Path("/tmp/test")
        project_id = "abc123"
        storage_dir = _get_storage_dir(base, project_id)
        assert storage_dir == base / "projects" / project_id

    def test_get_project_state_path(self):
        """State file path format is correct."""
        base = Path("/tmp/test")
        project_id = "abc123"
        state_path = _get_project_state_path(base, project_id)
        assert state_path == base / "projects" / project_id / "project_state.json"

    def test_quarantine_file(self, temp_base_dir):
        """Quarantine moves file with descriptive name."""
        project_id = "quarantine-test"
        storage_dir = _get_storage_dir(temp_base_dir, project_id)
        storage_dir.mkdir(parents=True, exist_ok=True)
        state_path = _get_project_state_path(temp_base_dir, project_id)
        state_path.write_text("test content")

        quarantine_path = _quarantine_file(temp_base_dir, project_id, state_path, "test_reason")

        assert not state_path.exists()
        assert quarantine_path.exists()
        assert "test_reason" in quarantine_path.name
        # Quarantine dir is under the project's storage directory
        assert quarantine_path.parent == storage_dir / "quarantine"


# ============================================================================
# Schema Version Tests
# ============================================================================

class TestSchemaVersion:
    """Test schema version handling."""

    def test_current_schema_version_constant(self):
        """CURRENT_SCHEMA_VERSION is defined."""
        assert CURRENT_SCHEMA_VERSION == "2.0"

    def test_get_supported_versions(self):
        """Supported versions list includes current."""
        versions = get_supported_schema_versions()
        assert CURRENT_SCHEMA_VERSION in versions


# ============================================================================
# Migration Tests
# ============================================================================

class TestMigration:
    """Test state migration."""

    def test_migrate_same_version_no_change(self, sample_project):
        """Migrating same version returns data unchanged."""
        data = sample_project.to_dict()
        data["schema_version"] = CURRENT_SCHEMA_VERSION

        from src.persistence import migrate_project_state_if_needed
        result = migrate_project_state_if_needed(data)

        assert result == data

    def test_migrate_unknown_version_passes_through(self, sample_project):
        """Unknown version passes through (validation handles it)."""
        data = sample_project.to_dict()
        data["schema_version"] = "99.0"

        from src.persistence import migrate_project_state_if_needed
        result = migrate_project_state_if_needed(data)

        assert result == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
