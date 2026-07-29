"""
Tests for Relay State Machine - Section 10, 16.2
"""

import pytest

from src.domain import (
    AssetKind,
    AssetRef,
    AssetScope,
    InputMode,
    Project,
    Scene,
    ScenePlan,
    SceneStatus,
    StyleBible,
    WorkflowMode,
)
from src.relay_state import (
    RelayStateMachine,
    TransitionError,
    can_transition,
    get_initial_status,
    validate_project_flow,
)


@pytest.fixture
def relay_project() -> Project:
    """Create a 3-scene relay mode project."""
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

    scenes = []
    for i in range(1, 4):
        asset = AssetRef(
            logical_id=f"scene_{i:02d}_master",
            kind=AssetKind.IMAGE,
            scope=AssetScope.SCENE,
            flow_asset_label=f"Scene {i} input",
            local_path=None,
            source_scene_id=i,
            confirmed_by_user=False,
        )

        scene = Scene(
            id=i,
            name=f"Scene {i}",
            input_mode=InputMode.MASTER_IMAGE if i == 1 else InputMode.PREVIOUS_FINAL_FRAME,
            asset_ref=asset,
            first_frame_prompt="First frame" if i == 1 else "",
            video_prompt=f"Video prompt {i}",
            template_exclusions="exclusions",
            negative_prompt="negative",
            clip_duration_seconds=10,
            lineage_revision="sha256:" + "0" * 64,
            status=SceneStatus.LOCKED,
        )
        scenes.append(scene)

    project = Project(
        schema_version="2.0",
        topic="test",
        topic_label="Test",
        genre="architecture",
        subtype="test",
        profile_id="architecture.korean",
        profile_version="2.0.0",
        workflow_mode=WorkflowMode.REFERENCE_FRAME_RELAY,
        duration_seconds=30,
        clip_duration_seconds=10,
        style_bible=style_bible,
        derived_fields={},
        scene_plans=[
            ScenePlan(1, "S1", "start", ["a"], "end", InputMode.MASTER_IMAGE),
            ScenePlan(2, "S2", "start", ["b"], "end", InputMode.PREVIOUS_FINAL_FRAME),
            ScenePlan(3, "S3", "start", ["c"], "end", InputMode.PREVIOUS_FINAL_FRAME),
        ],
        scene_count=3,
        source_revision="sha256:" + "0" * 64,
        flow_execution_profile_id="test",
        nim_enabled=False,
    )
    project.scenes = scenes
    project.source_revision = project.compute_source_revision()
    return project


@pytest.fixture
def single_clip_project() -> Project:
    """Create a single-clip project."""
    style_bible = StyleBible(
        identity_lock="Test",
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
        first_frame_prompt="First frame",
        video_prompt="Video prompt",
        template_exclusions="exclusions",
        negative_prompt="negative",
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
    project.source_revision = project.compute_source_revision()
    return project


class TestInitialStatus:
    """Test initial status determination."""

    def test_scene1_relay_no_master(self):
        """Scene 1 relay without master image → AWAITING_MASTER_IMAGE."""
        status = get_initial_status(0, WorkflowMode.REFERENCE_FRAME_RELAY, False, False)
        assert status == SceneStatus.AWAITING_MASTER_IMAGE

    def test_scene1_relay_with_master(self):
        """Scene 1 relay with master image → VIDEO_READY."""
        status = get_initial_status(0, WorkflowMode.REFERENCE_FRAME_RELAY, True, False)
        assert status == SceneStatus.VIDEO_READY

    def test_scene1_single_clip_no_master(self):
        """Scene 1 single-clip without master → AWAITING_MASTER_IMAGE."""
        status = get_initial_status(0, WorkflowMode.SINGLE_CLIP_FROM_MASTER, False, False)
        assert status == SceneStatus.AWAITING_MASTER_IMAGE

    def test_scene2_relay_no_prev(self):
        """Scene 2 relay without previous frame → AWAITING_PREVIOUS_FRAME."""
        status = get_initial_status(1, WorkflowMode.REFERENCE_FRAME_RELAY, False, False)
        assert status == SceneStatus.AWAITING_PREVIOUS_FRAME

    def test_scene2_relay_with_prev(self):
        """Scene 2 relay with previous frame → VIDEO_READY."""
        status = get_initial_status(1, WorkflowMode.REFERENCE_FRAME_RELAY, False, True)
        assert status == SceneStatus.VIDEO_READY


class TestTransitions:
    """Test valid/invalid transitions."""

    def test_valid_locked_to_awaiting_master(self):
        assert can_transition(SceneStatus.LOCKED, SceneStatus.AWAITING_MASTER_IMAGE)

    def test_valid_awaiting_master_to_video_ready(self):
        assert can_transition(SceneStatus.AWAITING_MASTER_IMAGE, SceneStatus.VIDEO_READY)

    def test_valid_video_ready_to_confirmed(self):
        assert can_transition(SceneStatus.VIDEO_READY, SceneStatus.CONFIRMED)

    def test_valid_confirmed_to_complete(self):
        assert can_transition(SceneStatus.CONFIRMED, SceneStatus.COMPLETE)

    def test_valid_complete_to_needs_retry(self):
        assert can_transition(SceneStatus.COMPLETE, SceneStatus.NEEDS_RETRY)

    def test_valid_needs_retry_to_locked(self):
        assert can_transition(SceneStatus.NEEDS_RETRY, SceneStatus.LOCKED)

    def test_invalid_locked_to_complete(self):
        assert not can_transition(SceneStatus.LOCKED, SceneStatus.COMPLETE)

    def test_invalid_awaiting_to_complete(self):
        assert not can_transition(SceneStatus.AWAITING_MASTER_IMAGE, SceneStatus.COMPLETE)

    def test_invalid_video_ready_to_locked(self):
        assert not can_transition(SceneStatus.VIDEO_READY, SceneStatus.LOCKED)


class TestRelayStateMachine:
    """Test relay state machine behavior."""

    def test_initial_branch_created(self, relay_project: Project):
        """Initial branch created with correct default statuses."""
        sm = RelayStateMachine(relay_project)
        branch = sm.current_branch

        assert branch is not None
        assert branch.branch_id is not None
        assert branch.parent_branch_id is None
        # Scene 1 has no master image → AWAITING_MASTER_IMAGE
        assert branch.scene_statuses["1"] == SceneStatus.AWAITING_MASTER_IMAGE
        # Scenes 2,3 have no previous frame → AWAITING_PREVIOUS_FRAME
        assert branch.scene_statuses["2"] == SceneStatus.AWAITING_PREVIOUS_FRAME
        assert branch.scene_statuses["3"] == SceneStatus.AWAITING_PREVIOUS_FRAME

    def test_scene_views(self, relay_project: Project):
        """Get scene views for UI."""
        sm = RelayStateMachine(relay_project)
        views = sm.get_all_views()

        assert len(views) == 3
        assert views[0].scene_id == 1
        assert views[0].status == SceneStatus.AWAITING_MASTER_IMAGE
        assert views[0].input_mode_value == "MASTER_IMAGE"
        assert views[1].status == SceneStatus.AWAITING_PREVIOUS_FRAME
        assert views[1].input_mode_value == "PREVIOUS_FINAL_FRAME"

    def test_on_asset_confirmed_scene1(self, relay_project: Project):
        """Confirming master image on scene 1 → VIDEO_READY."""
        sm = RelayStateMachine(relay_project)
        sm.on_asset_confirmed(1, "scenes/master_confirmed.png")

        view = sm.get_scene_view(1)
        assert view.status == SceneStatus.VIDEO_READY
        assert relay_project.scenes[0].asset_ref.local_path == "scenes/master_confirmed.png"
        assert relay_project.scenes[0].asset_ref.confirmed_by_user is True

    def test_on_asset_confirmed_scene2(self, relay_project: Project):
        """Confirming previous frame on scene 2 → VIDEO_READY."""
        sm = RelayStateMachine(relay_project)
        # First confirm scene 1
        sm.on_asset_confirmed(1, "master.png")
        # Then confirm scene 2's previous frame
        sm.on_asset_confirmed(2, "scene_01_last_frame.png")

        view2 = sm.get_scene_view(2)
        assert view2.status == SceneStatus.VIDEO_READY

    def test_on_video_generated(self, relay_project: Project):
        """Video generation completes → VIDEO_READY (already there) or CONFIRMED."""
        sm = RelayStateMachine(relay_project)
        sm.on_asset_confirmed(1, "master.png")
        sm.on_video_generated(1, "output/video_01.mp4")

        view = sm.get_scene_view(1)
        assert view.status == SceneStatus.VIDEO_READY
        # Asset should be updated to video
        assert relay_project.scenes[0].asset_ref.local_path == "output/video_01.mp4"
        assert relay_project.scenes[0].asset_ref.kind == AssetKind.VIDEO

    def test_on_user_confirm_accept(self, relay_project: Project):
        """User accepts video → CONFIRMED, next scene unlocked."""
        sm = RelayStateMachine(relay_project)
        sm.on_asset_confirmed(1, "master.png")
        sm.on_video_generated(1, "video_01.mp4")
        sm.on_user_confirm(1, accept=True)

        view1 = sm.get_scene_view(1)
        assert view1.status == SceneStatus.CONFIRMED
        assert relay_project.scenes[0].status == SceneStatus.CONFIRMED

        # Scene 2 should now be AWAITING_PREVIOUS_FRAME (waiting for frame)
        view2 = sm.get_scene_view(2)
        assert view2.status == SceneStatus.AWAITING_PREVIOUS_FRAME

    def test_on_user_confirm_reject(self, relay_project: Project):
        """User rejects video → NEEDS_RETRY."""
        sm = RelayStateMachine(relay_project)
        sm.on_asset_confirmed(1, "master.png")
        sm.on_video_generated(1, "video_01.mp4")
        sm.on_user_confirm(1, accept=False)

        view = sm.get_scene_view(1)
        assert view.status == SceneStatus.NEEDS_RETRY

    def test_on_retry_requested(self, relay_project: Project):
        """Retry from VIDEO_READY → NEEDS_RETRY."""
        sm = RelayStateMachine(relay_project)
        sm.on_asset_confirmed(1, "master.png")
        sm.on_video_generated(1, "video_01.mp4")
        sm.on_retry_requested(1)

        view = sm.get_scene_view(1)
        assert view.status == SceneStatus.NEEDS_RETRY

    def test_invalid_transition_raises(self, relay_project: Project):
        """Invalid direct transition raises TransitionError."""
        sm = RelayStateMachine(relay_project)
        # Try to jump LOCKED -> CONFIRMED (invalid)
        with pytest.raises(TransitionError):
            sm.transition(1, SceneStatus.CONFIRMED)

    def test_force_transition_works(self, relay_project: Project):
        """Force flag bypasses validation (for recovery)."""
        sm = RelayStateMachine(relay_project)
        sm.transition(1, SceneStatus.CONFIRMED, force=True)
        view = sm.get_scene_view(1)
        assert view.status == SceneStatus.CONFIRMED

    def test_get_next_actionable_scene(self, relay_project: Project):
        """Get next scene needing user action."""
        sm = RelayStateMachine(relay_project)
        # Scene 1 needs master image
        assert sm.get_next_actionable_scene() == 1

        sm.on_asset_confirmed(1, "master.png")
        # Scene 1 ready for video gen
        assert sm.get_next_actionable_scene() == 1

        sm.on_video_generated(1, "video.mp4")
        # Scene 1 needs confirmation
        assert sm.get_next_actionable_scene() == 1

    def test_is_all_complete(self, relay_project: Project):
        """Check all complete."""
        sm = RelayStateMachine(relay_project)
        assert not sm.is_all_complete()

        # Complete all scenes
        for i in range(1, 4):
            sm.on_asset_confirmed(i, f"asset_{i}.png")
            sm.on_video_generated(i, f"video_{i}.mp4")
            sm.on_user_confirm(i, accept=True)

        assert sm.is_all_complete()


class TestCascadingEffects:
    """Test cascade effects (STALE, auto-unlock)."""

    def test_stale_cascades_downstream(self, relay_project: Project):
        """Marking scene 1 STALE cascades to scenes 2,3."""
        sm = RelayStateMachine(relay_project)
        sm.on_asset_confirmed(1, "master.png")
        sm.on_video_generated(1, "video_1.mp4")
        sm.on_user_confirm(1, True)

        sm.on_asset_confirmed(2, "frame_1.png")
        sm.on_video_generated(2, "video_2.mp4")
        sm.on_user_confirm(2, True)

        sm.on_asset_confirmed(3, "frame_2.png")
        sm.on_video_generated(3, "video_3.mp4")
        sm.on_user_confirm(3, True)

        # All complete
        assert sm.is_all_complete()

        # Mark scene 1 stale (simulate upstream change)
        sm.transition(1, SceneStatus.STALE, force=True)

        # Downstream should be STALE
        assert sm.get_scene_view(2).status == SceneStatus.STALE
        assert sm.get_scene_view(3).status == SceneStatus.STALE

    def test_upstream_reconfirm_marks_downstream_stale(self, relay_project: Project):
        """Re-confirming scene 1 marks downstream STALE."""
        sm = RelayStateMachine(relay_project)
        sm.on_asset_confirmed(1, "master.png")
        sm.on_video_generated(1, "video_1.mp4")
        sm.on_user_confirm(1, True)
        sm.on_asset_confirmed(2, "frame_1.png")
        sm.on_video_generated(2, "video_2.mp4")
        sm.on_user_confirm(2, True)

        # Now re-confirm scene 1 (new master image)
        sm.on_video_generated(1, "video_1_new.mp4")
        sm.on_user_confirm(1, True)

        # Scene 2 should be STALE
        assert sm.get_scene_view(2).status == SceneStatus.STALE

    def test_check_stale_against_source_revision(self, relay_project: Project):
        """check_stale finds scenes with different lineage."""
        sm = RelayStateMachine(relay_project)
        sm.on_asset_confirmed(1, "master.png")
        sm.on_video_generated(1, "video_1.mp4")
        sm.on_user_confirm(1, True)

        # Change project source revision
        relay_project.source_revision = "sha256:" + "1" * 64

        # Check stale
        stale = sm.check_stale(relay_project.source_revision)
        assert 1 in stale
        assert sm.get_scene_view(1).status == SceneStatus.STALE


class TestBranching:
    """Test branch preservation (Section 16.2)."""

    def test_create_branch_preserves_history(self, relay_project: Project):
        """Creating branch preserves asset refs up to parent."""
        sm = RelayStateMachine(relay_project)
        sm.on_asset_confirmed(1, "master.png")
        sm.on_video_generated(1, "video_1.mp4")
        sm.on_user_confirm(1, True)
        sm.on_asset_confirmed(2, "frame_1.png")

        # Save old branch ID before creating new branch
        old_branch_id = sm.current_branch.branch_id

        # Create branch at scene 2
        new_branch = sm.create_branch(parent_scene_id=2)

        # New branch should have parent's assets up to scene 2
        assert new_branch.parent_branch_id == old_branch_id
        # And it should be the active branch
        assert relay_project.relay_branch == new_branch

    def test_branch_statuses_reset_after_parent(self, relay_project: Project):
        """New branch resets statuses after parent scene."""
        sm = RelayStateMachine(relay_project)
        sm.on_asset_confirmed(1, "master.png")
        sm.on_video_generated(1, "video_1.mp4")
        sm.on_user_confirm(1, True)

        new_branch = sm.create_branch(parent_scene_id=1)

        # Scene 1 keeps its status (CONFIRMED, since only 1 scene confirmed so far)
        assert new_branch.scene_statuses["1"] == SceneStatus.CONFIRMED
        # Scene 2 reset to initial
        assert new_branch.scene_statuses["2"] == SceneStatus.AWAITING_PREVIOUS_FRAME
        # Scene 3 reset
        assert new_branch.scene_statuses["3"] == SceneStatus.AWAITING_PREVIOUS_FRAME


class TestValidateFlow:
    """Test project flow validation."""

    def test_valid_relay_flow(self, relay_project: Project):
        """Valid project with all assets confirmed."""
        sm = RelayStateMachine(relay_project)
        sm.on_asset_confirmed(1, "master.png")
        sm.on_asset_confirmed(2, "frame_1.png")
        sm.on_asset_confirmed(3, "frame_2.png")

        errors = validate_project_flow(relay_project)
        assert errors == []

    def test_missing_master_image(self, relay_project: Project):
        """Missing master image on scene 1 → error."""
        relay_project.scenes[0].asset_ref.local_path = None
        errors = validate_project_flow(relay_project)
        assert any("master image" in e.lower() for e in errors)

    def test_wrong_input_mode(self, relay_project: Project):
        """Wrong input mode on relay scene → error."""
        relay_project.scenes[1].input_mode = InputMode.MASTER_IMAGE
        errors = validate_project_flow(relay_project)
        assert any("input_mode" in e for e in errors)

    def test_lineage_mismatch(self, relay_project: Project):
        """Lineage revision mismatch → error."""
        sm = RelayStateMachine(relay_project)
        sm.on_asset_confirmed(1, "master.png")
        sm.on_video_generated(1, "video_1.mp4")
        sm.on_user_confirm(1, True)
        # Change source revision
        relay_project.source_revision = "sha256:" + "1" * 64

        errors = validate_project_flow(relay_project)
        assert any("lineage_revision" in e for e in errors)

    def test_status_consistency(self, relay_project: Project):
        """Branch status must match scene status."""
        sm = RelayStateMachine(relay_project)
        sm.on_asset_confirmed(1, "master.png")
        # Force branch to different status
        sm.current_branch.scene_statuses["1"] = SceneStatus.LOCKED

        errors = validate_project_flow(relay_project)
        assert any("branch status" in e.lower() for e in errors)


class TestSingleClipMode:
    """Test SINGLE_CLIP_FROM_MASTER mode."""

    def test_single_clip_initial(self, single_clip_project: Project):
        """Single clip project with master image → VIDEO_READY."""
        sm = RelayStateMachine(single_clip_project)
        view = sm.get_scene_view(1)
        assert view.status == SceneStatus.VIDEO_READY

    def test_single_clip_no_master(self, single_clip_project: Project):
        """Single clip without master → AWAITING_MASTER_IMAGE."""
        project = single_clip_project
        project.scenes[0].asset_ref.local_path = None
        sm = RelayStateMachine(project)
        view = sm.get_scene_view(1)
        assert view.status == SceneStatus.AWAITING_MASTER_IMAGE
