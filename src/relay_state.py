"""
Relay State Machine - Section 10, 16.2

Implements the Scene-level state machine for Reference-Frame Relay workflow:
LOCKED → AWAITING_MASTER_IMAGE / AWAITING_PREVIOUS_FRAME → VIDEO_READY → CONFIRMED → COMPLETE
                    ↑________ NEEDS_RETRY ________↓           ↑____ STALE ____↓

Also implements RelayBranch for branch preservation (Section 16.2):
- Each project edit creates a new branch preserving previous attempts
- Branches form a tree: branch_id → parent_branch_id
- Assets are tracked per-branch for continuity
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from .domain import (
    SceneStatus,
    AssetRef,
    AssetKind,
    AssetScope,
    RelayBranch,
    Project,
    WorkflowMode,
    InputMode,
)


class TransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, from_state: SceneStatus, to_state: SceneStatus, reason: str):
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason
        super().__init__(f"Invalid transition {from_state} -> {to_state}: {reason}")


# Valid state transitions per Section 10.3 mermaid diagram
VALID_TRANSITIONS: dict[SceneStatus, set[SceneStatus]] = {
    SceneStatus.LOCKED: {
        SceneStatus.AWAITING_MASTER_IMAGE,
        SceneStatus.AWAITING_PREVIOUS_FRAME,
        SceneStatus.NEEDS_RETRY,
    },
    SceneStatus.AWAITING_MASTER_IMAGE: {
        SceneStatus.VIDEO_READY,
        SceneStatus.NEEDS_RETRY,
        SceneStatus.LOCKED,  # User cancels
    },
    SceneStatus.AWAITING_PREVIOUS_FRAME: {
        SceneStatus.VIDEO_READY,
        SceneStatus.NEEDS_RETRY,
        SceneStatus.LOCKED,  # User cancels
    },
    SceneStatus.VIDEO_READY: {
        SceneStatus.CONFIRMED,
        SceneStatus.NEEDS_RETRY,  # Re-render
    },
    SceneStatus.CONFIRMED: {
        SceneStatus.COMPLETE,
        SceneStatus.NEEDS_RETRY,  # User rejects, re-render
    },
    SceneStatus.COMPLETE: {
        SceneStatus.NEEDS_RETRY,  # Global re-render
        SceneStatus.STALE,        # Upstream changed
    },
    SceneStatus.NEEDS_RETRY: {
        SceneStatus.AWAITING_MASTER_IMAGE,
        SceneStatus.AWAITING_PREVIOUS_FRAME,
        SceneStatus.LOCKED,
    },
    SceneStatus.STALE: {
        SceneStatus.LOCKED,  # Reset after upstream sync
    },
}


def can_transition(from_state: SceneStatus, to_state: SceneStatus) -> bool:
    """Check if transition is valid per state machine."""
    return to_state in VALID_TRANSITIONS.get(from_state, set())


def get_initial_status(
    scene_index: int,
    workflow_mode: WorkflowMode,
    has_master_image: bool = False,
    has_previous_frame: bool = False,
) -> SceneStatus:
    """
    Determine initial scene status based on position and workflow.

    Scene 1 in relay mode: AWAITING_MASTER_IMAGE if no image, VIDEO_READY if has image
    Scene 1 in single-clip: AWAITING_MASTER_IMAGE
    Scene N>1 in relay mode: AWAITING_PREVIOUS_FRAME
    Scene N>1 in single-clip: LOCKED (not used)
    """
    if scene_index == 0:  # Scene 1
        if workflow_mode == WorkflowMode.REFERENCE_FRAME_RELAY:
            if has_master_image:
                return SceneStatus.VIDEO_READY
            return SceneStatus.AWAITING_MASTER_IMAGE
        else:  # SINGLE_CLIP_FROM_MASTER
            if has_master_image:
                return SceneStatus.VIDEO_READY
            return SceneStatus.AWAITING_MASTER_IMAGE
    else:  # Scene 2+
        if workflow_mode == WorkflowMode.REFERENCE_FRAME_RELAY:
            if has_previous_frame:
                return SceneStatus.VIDEO_READY
            return SceneStatus.AWAITING_PREVIOUS_FRAME
        else:
            return SceneStatus.LOCKED


@dataclass
class SceneStateView:
    """Read-only view of a scene's state for UI/Runner."""
    scene_id: int
    name: str
    status: SceneStatus
    input_mode_value: str  # "MASTER_IMAGE" or "PREVIOUS_FINAL_FRAME" or "NONE"
    asset_label: str
    video_ready: bool
    can_retry: bool
    can_confirm: bool
    is_stale: bool = False
    error_message: Optional[str] = None


class RelayStateMachine:
    """
    Scene-level state machine enforcing valid transitions.

    In REFERENCE_FRAME_RELAY mode:
    - Scene 1: LOCKED → AWAITING_MASTER_IMAGE → VIDEO_READY → CONFIRMED → COMPLETE
    - Scene N>1: LOCKED → AWAITING_PREVIOUS_FRAME → VIDEO_READY → CONFIRMED → COMPLETE

    Transitions are triggered by:
    - User providing master image (asset confirmed)
    - Previous scene's final frame being available (asset confirmed)
    - Video generation completing
    - User confirming/rejecting video
    - Upstream changes invalidating downstream (STALE)
    """

    def __init__(self, project: Project):
        self.project = project
        self._branch = project.relay_branch or self._create_initial_branch()
        project.relay_branch = self._branch

    def _create_initial_branch(self) -> RelayBranch:
        """Create initial relay branch for new project."""
        now = datetime.utcnow()
        scene_statuses = {}
        for i, scene in enumerate(self.project.scenes):
            has_master = scene.asset_ref.local_path is not None if scene.id == 1 else False
            has_prev = scene.asset_ref.local_path is not None if scene.id > 1 else False
            scene_statuses[str(scene.id)] = get_initial_status(
                i, self.project.workflow_mode, has_master, has_prev
            )

        return RelayBranch(
            branch_id=str(uuid.uuid4()),
            parent_branch_id=None,
            scene_statuses=scene_statuses,
            asset_refs=[s.asset_ref for s in self.project.scenes],
            created_at=now,
            lineage_revision=self.project.source_revision,
            nonce=str(uuid.uuid4())[:8],
        )

    def get_scene_view(self, scene_id: int) -> SceneStateView:
        """Get read-only view of scene state for UI."""
        scene = next((s for s in self.project.scenes if s.id == scene_id), None)
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")

        status = self._branch.scene_statuses.get(str(scene_id), SceneStatus.LOCKED)
        is_first = scene_id == 1
        input_mode = "MASTER_IMAGE" if is_first else "PREVIOUS_FINAL_FRAME"

        return SceneStateView(
            scene_id=scene_id,
            name=scene.name,
            status=status,
            input_mode_value=input_mode if self.project.workflow_mode == WorkflowMode.REFERENCE_FRAME_RELAY else "NONE",
            asset_label=scene.asset_ref.flow_asset_label,
            video_ready=status == SceneStatus.VIDEO_READY,
            can_retry=status in (SceneStatus.VIDEO_READY, SceneStatus.CONFIRMED, SceneStatus.COMPLETE, SceneStatus.NEEDS_RETRY, SceneStatus.STALE),
            can_confirm=status == SceneStatus.VIDEO_READY,
        )

    def get_all_views(self) -> list[SceneStateView]:
        """Get all scene views in order."""
        return [self.get_scene_view(s.id) for s in sorted(self.project.scenes, key=lambda s: s.id)]

    def transition(self, scene_id: int, new_status: SceneStatus, *, force: bool = False) -> None:
        """
        Transition scene to new status.

        Args:
            scene_id: Scene to transition
            new_status: Target status
            force: Allow invalid transitions (for recovery/admin only)

        Raises:
            TransitionError: If transition is invalid
        """
        current = self._branch.scene_statuses.get(str(scene_id), SceneStatus.LOCKED)

        if current == new_status:
            return  # No-op

        if not force and not can_transition(current, new_status):
            raise TransitionError(current, new_status, "Not allowed by state machine")

        self._branch.scene_statuses[str(scene_id)] = new_status

        # Update scene object
        scene = next((s for s in self.project.scenes if s.id == scene_id), None)
        if scene:
            scene.status = new_status

        # Handle cascade effects
        self._handle_transition_effects(scene_id, current, new_status)

    def _handle_transition_effects(
        self, scene_id: int, from_status: SceneStatus, to_status: SceneStatus
    ) -> None:
        """Handle cascade effects of state transitions."""
        # Scene confirmed complete → unlock next scene in relay mode
        if to_status == SceneStatus.CONFIRMED and self.project.workflow_mode == WorkflowMode.REFERENCE_FRAME_RELAY:
            next_scene_id = scene_id + 1
            if next_scene_id <= len(self.project.scenes):
                next_status = self._branch.scene_statuses.get(str(next_scene_id), SceneStatus.LOCKED)
                if next_status == SceneStatus.LOCKED:
                    # Check if we have the previous frame asset
                    next_scene = next((s for s in self.project.scenes if s.id == next_scene_id), None)
                    if next_scene and next_scene.asset_ref.local_path:
                        # Previous frame is available → jump to VIDEO_READY
                        self.transition(next_scene_id, SceneStatus.VIDEO_READY, force=True)
                    else:
                        # Wait for previous frame
                        self.transition(next_scene_id, SceneStatus.AWAITING_PREVIOUS_FRAME, force=True)

        # Scene marked STALE → mark downstream as STALE
        if to_status == SceneStatus.STALE:
            for s in self.project.scenes:
                if s.id > scene_id:
                    self.transition(s.id, SceneStatus.STALE, force=True)

        # Upstream change detected (e.g., Scene 1 re-confirmed) → downstream to STALE
        if scene_id == 1 and to_status == SceneStatus.CONFIRMED:
            for s in self.project.scenes:
                if s.id > 1:
                    current = self._branch.scene_statuses.get(str(s.id))
                    if current in (SceneStatus.CONFIRMED, SceneStatus.COMPLETE):
                        self.transition(s.id, SceneStatus.STALE, force=True)

    def on_asset_confirmed(self, scene_id: int, asset_path: str) -> None:
        """
        Called when user confirms an asset (master image or previous frame).

        Updates asset_ref and transitions scene accordingly.
        """
        scene = next((s for s in self.project.scenes if s.id == scene_id), None)
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")

        # Update asset ref
        scene.asset_ref.local_path = asset_path
        scene.asset_ref.confirmed_by_user = True
        scene.asset_ref.confirmed_at = datetime.utcnow()

        # Update branch asset refs
        for ar in self._branch.asset_refs:
            if ar.logical_id == scene.asset_ref.logical_id:
                ar.local_path = asset_path
                ar.confirmed_by_user = True
                ar.confirmed_at = datetime.utcnow()
                break

        # Transition based on scene role
        current = self._branch.scene_statuses.get(str(scene_id), SceneStatus.LOCKED)

        if scene_id == 1:
            if current in (SceneStatus.LOCKED, SceneStatus.AWAITING_MASTER_IMAGE):
                self.transition(scene_id, SceneStatus.VIDEO_READY)
        else:
            if current in (SceneStatus.LOCKED, SceneStatus.AWAITING_PREVIOUS_FRAME):
                self.transition(scene_id, SceneStatus.VIDEO_READY)

    def on_video_generated(self, scene_id: int, video_path: str) -> None:
        """
        Called when video generation completes for a scene.

        Updates lineage_revision and transitions to VIDEO_READY.
        """
        scene = next((s for s in self.project.scenes if s.id == scene_id), None)
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")

        # Update asset with video path
        video_asset = AssetRef(
            logical_id=f"scene_{scene_id:02d}_video",
            kind=AssetKind.VIDEO,
            scope=AssetScope.SCENE,
            flow_asset_label=f"Scene {scene_id} video",
            local_path=video_path,
            source_scene_id=scene_id,
            confirmed_by_user=True,
            confirmed_at=datetime.utcnow(),
        )
        scene.asset_ref = video_asset
        scene.status = SceneStatus.VIDEO_READY
        scene.confirmed_at = None  # Will be set on confirm

        # Update branch
        self._branch.asset_refs.append(video_asset)
        self._branch.scene_statuses[str(scene_id)] = SceneStatus.VIDEO_READY

    def on_user_confirm(self, scene_id: int, accept: bool = True) -> None:
        """
        Called when user confirms or rejects a generated video.

        accept=True: CONFIRMED → may unlock next scene; auto-complete if all done
        accept=False: NEEDS_RETRY
        """
        current = self._branch.scene_statuses.get(str(scene_id))
        if current != SceneStatus.VIDEO_READY:
            raise TransitionError(
                current or SceneStatus.LOCKED,
                SceneStatus.CONFIRMED if accept else SceneStatus.NEEDS_RETRY,
                "Can only confirm from VIDEO_READY"
            )

        if accept:
            scene = next((s for s in self.project.scenes if s.id == scene_id), None)
            if scene:
                scene.status = SceneStatus.CONFIRMED
                scene.confirmed_at = datetime.utcnow()
                scene.lineage_revision = self.project.compute_source_revision()
            self.transition(scene_id, SceneStatus.CONFIRMED)
            # Auto-complete: if ALL scenes are now CONFIRMED or COMPLETE, transition all CONFIRMED to COMPLETE
            if self._all_scenes_at_least_confirmed():
                for s in self.project.scenes:
                    if self._branch.scene_statuses.get(str(s.id)) == SceneStatus.CONFIRMED:
                        self.transition(s.id, SceneStatus.COMPLETE, force=True)
        else:
            self.transition(scene_id, SceneStatus.NEEDS_RETRY)

    def _all_scenes_at_least_confirmed(self) -> bool:
        """Check if all scenes are CONFIRMED or COMPLETE (eligible for auto-complete)."""
        for scene in self.project.scenes:
            status = self._branch.scene_statuses.get(str(scene.id), SceneStatus.LOCKED)
            if status not in (SceneStatus.CONFIRMED, SceneStatus.COMPLETE):
                return False
        return True

    def on_retry_requested(self, scene_id: int) -> None:
        """User requests re-render of a scene."""
        current = self._branch.scene_statuses.get(str(scene_id))
        if current not in (SceneStatus.VIDEO_READY, SceneStatus.CONFIRMED, SceneStatus.COMPLETE, SceneStatus.NEEDS_RETRY):
            raise TransitionError(
                current or SceneStatus.LOCKED,
                SceneStatus.NEEDS_RETRY,
                f"Retry not allowed from {current}"
            )
        self.transition(scene_id, SceneStatus.NEEDS_RETRY)

    def is_all_complete(self) -> bool:
        """Check if all scenes are COMPLETE."""
        for scene in self.project.scenes:
            status = self._branch.scene_statuses.get(str(scene.id))
            if status != SceneStatus.COMPLETE:
                return False
        return True

    def get_next_actionable_scene(self) -> Optional[int]:
        """Get the next scene that needs user action (in order)."""
        for scene in sorted(self.project.scenes, key=lambda s: s.id):
            status = self._branch.scene_statuses.get(str(scene.id), SceneStatus.LOCKED)
            if status in (SceneStatus.AWAITING_MASTER_IMAGE, SceneStatus.AWAITING_PREVIOUS_FRAME):
                return scene.id
            if status == SceneStatus.VIDEO_READY:
                return scene.id
        return None

    def check_stale(self, current_source_revision: str) -> list[int]:
        """
        Check for stale scenes against current source revision.

        Returns list of scene IDs that are stale (branch lineage_revision != current).
        """
        stale = []
        if self._branch.lineage_revision != current_source_revision:
            for scene in self.project.scenes:
                status = self._branch.scene_statuses.get(str(scene.id))
                if status in (SceneStatus.CONFIRMED, SceneStatus.COMPLETE):
                    stale.append(scene.id)
                    self.transition(scene.id, SceneStatus.STALE, force=True)
        return stale

    def create_branch(self, *, parent_scene_id: int, reason: str = "retry") -> RelayBranch:
        """
        Create a new branch from current state (Section 16.2).

        When user retries a scene, we preserve the current branch
        and create a new one with:
        - Same asset refs up to parent_scene_id
        - Reset statuses for parent_scene_id onwards
        """
        # Save old branch ID before switching
        old_branch_id = self._branch.branch_id

        new_branch = RelayBranch(
            branch_id=str(uuid.uuid4()),
            parent_branch_id=old_branch_id,
            scene_statuses={},
            asset_refs=[],
            created_at=datetime.utcnow(),
            lineage_revision=self.project.source_revision,
            nonce=str(uuid.uuid4())[:8],
        )

        # Copy asset refs up to parent_scene_id
        for ar in self._branch.asset_refs:
            if ar.source_scene_id and ar.source_scene_id <= parent_scene_id:
                new_branch.asset_refs.append(ar)

        # Copy statuses up to parent_scene_id, reset rest to initial
        for scene in self.project.scenes:
            if scene.id <= parent_scene_id:
                new_branch.scene_statuses[str(scene.id)] = self._branch.scene_statuses.get(
                    str(scene.id), SceneStatus.LOCKED
                )
            else:
                # Determine initial status based on assets
                if scene.id == 1:
                    has_master = scene.asset_ref.local_path is not None
                    new_branch.scene_statuses[str(scene.id)] = get_initial_status(
                        0, self.project.workflow_mode, has_master, False
                    )
                else:
                    has_prev = scene.asset_ref.local_path is not None
                    new_branch.scene_statuses[str(scene.id)] = get_initial_status(
                        scene.id - 1, self.project.workflow_mode, False, has_prev
                    )

        # Switch project to new branch
        self._branch = new_branch
        self.project.relay_branch = new_branch
        return new_branch

    @property
    def current_branch(self) -> RelayBranch:
        return self._branch


def validate_project_flow(project: Project) -> list[str]:
    """
    Validate entire project flow invariants.

    Returns list of errors (empty = valid).
    """
    errors = []

    # 1. Scene 1 must have master image in relay mode
    if project.workflow_mode == WorkflowMode.REFERENCE_FRAME_RELAY:
        scene1 = next((s for s in project.scenes if s.id == 1), None)
        if scene1:
            if scene1.input_mode != InputMode.MASTER_IMAGE:
                errors.append("Scene 1 must have MASTER_IMAGE input_mode in relay mode")
            if not scene1.asset_ref or not scene1.asset_ref.local_path:
                errors.append("Scene 1 must have confirmed master image asset")

    # 2. Each relay scene must have confirmed previous frame
    for i, scene in enumerate(project.scenes):
        if i == 0:
            continue  # Scene 1 handled above
        if project.workflow_mode == WorkflowMode.REFERENCE_FRAME_RELAY:
            if scene.input_mode != InputMode.PREVIOUS_FINAL_FRAME:
                errors.append(f"Scene {scene.id} must have PREVIOUS_FINAL_FRAME input_mode in relay mode")
            if not scene.asset_ref or not scene.asset_ref.local_path:
                errors.append(f"Scene {scene.id} must have confirmed previous frame asset")

    # 3. Lineage revisions must match for confirmed scenes
    for scene in project.scenes:
        if scene.status in (SceneStatus.CONFIRMED, SceneStatus.COMPLETE):
            if scene.lineage_revision != project.source_revision:
                errors.append(f"Scene {scene.id}: lineage_revision {scene.lineage_revision} != project source_revision {project.source_revision}")

    # 4. Status consistency with branch
    if project.relay_branch:
        for scene in project.scenes:
            branch_status = project.relay_branch.scene_statuses.get(str(scene.id))
            if branch_status and branch_status != scene.status:
                errors.append(f"Scene {scene.id}: branch status {branch_status} != scene status {scene.status}")

    return errors