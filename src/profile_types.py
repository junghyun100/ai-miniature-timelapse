"""
Profile Types - Profile Registry and Interface Definitions

Per Section 13.1 of the Reference-Frame Relay Specification v2.0.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


class WorkflowMode(StrEnum):
    REFERENCE_FRAME_RELAY = "REFERENCE_FRAME_RELAY"
    SINGLE_CLIP_FROM_MASTER = "SINGLE_CLIP_FROM_MASTER"


class AspectRatio(StrEnum):
    RATIO_9_16 = "9:16"
    RATIO_16_9 = "16:9"
    RATIO_1_1 = "1:1"


class NimRefinementPolicy(StrEnum):
    MUTABLE_ONLY = "mutable_only"
    ALL = "all"


class ProvenanceSource(StrEnum):
    LOCAL_PLANNER = "local_planner"
    NVIDIA_NIM = "nvidia_nim"


class InputMode(StrEnum):
    MASTER_IMAGE = "MASTER_IMAGE"
    PREVIOUS_FINAL_FRAME = "PREVIOUS_FINAL_FRAME"
    NONE = "NONE"


class SceneStatus(StrEnum):
    LOCKED = "LOCKED"
    AWAITING_MASTER_IMAGE = "AWAITING_MASTER_IMAGE"
    AWAITING_PREVIOUS_FRAME = "AWAITING_PREVIOUS_FRAME"
    VIDEO_READY = "VIDEO_READY"
    CONFIRMED = "CONFIRMED"
    COMPLETE = "COMPLETE"
    NEEDS_RETRY = "NEEDS_RETRY"
    STALE = "STALE"


class AssetKind(StrEnum):
    IMAGE = "image"
    VIDEO = "video"


class AssetScope(StrEnum):
    PROJECT = "project"
    SCENE = "scene"


# Shared state continuity rule used across profiles.
STATE_PERMANENCE_RULE = (
    "keep every already-installed, already-placed, or already-prepared element visible and fixed; "
    "do not remove, swap, reset, or rebuild existing work; "
    "do not introduce later-stage parts, ingredients, or details before their turn"
)


# ============================================================================
# Domain Models
# ============================================================================


@dataclass
class StyleBible:
    identity_lock: str
    materials: dict
    camera: dict
    lighting: dict
    color_palette: dict
    workspace: dict
    hands_rule: str
    motion_rule: str
    negative_prompt_base: str

    def to_dict(self) -> dict:
        return {
            "identity_lock": self.identity_lock,
            "materials": self.materials,
            "camera": self.camera,
            "lighting": self.lighting,
            "color_palette": self.color_palette,
            "workspace": self.workspace,
            "hands_rule": self.hands_rule,
            "motion_rule": self.motion_rule,
            "negative_prompt_base": self.negative_prompt_base,
        }

    @classmethod
    def from_dict(cls, data: dict) -> StyleBible:
        return cls(**data)


@dataclass
class AssetRef:
    logical_id: str
    kind: AssetKind
    scope: AssetScope
    flow_asset_id: str | None = None
    flow_asset_label: str | None = None
    local_path: str | None = None
    source_scene_id: int | None = None
    confirmed_by_user: bool = False
    confirmed_at: datetime | None = None
    content_hash: str | None = None
    lineage_revision: str | None = None

    def to_dict(self) -> dict:
        d = {}
        for k, v in self.__dict__.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat()
            elif isinstance(v, Enum):
                d[k] = v.value
            else:
                d[k] = v
        return d

    @classmethod
    def from_dict(cls, data: dict) -> AssetRef:
        data = data.copy()
        if data.get("kind"):
            data["kind"] = AssetKind(data["kind"])
        if data.get("scope"):
            data["scope"] = AssetScope(data["scope"])
        if data.get("confirmed_at"):
            data["confirmed_at"] = datetime.fromisoformat(data["confirmed_at"])
        return cls(**data)


@dataclass
class ScenePlan:
    scene_id: int
    name: str
    start_state: str
    ordered_actions: list[str]
    end_state: str
    forbidden_changes: list[str]
    input_mode: InputMode = InputMode.NONE
    estimated_clip_duration_seconds: int = 10
    completion_range: str = ""
    is_final_scene: bool = False
    reserved_future_actions: list[str] = field(default_factory=list)
    forbidden_future_actions: list[str] = field(default_factory=list)
    exact_stop_state: str = ""
    visible_micro_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = dict(self.__dict__.items())
        d["input_mode"] = self.input_mode.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> ScenePlan:
        data = data.copy()
        input_mode = data.get("input_mode", InputMode.NONE)
        if not isinstance(input_mode, InputMode):
            input_mode = InputMode(input_mode)
        data["input_mode"] = input_mode
        return cls(**data)


def build_scene_control_block(
    scene_plan: ScenePlan | Any,
    user_overrides: dict[str, Any] | None = None,
    state_policy: str = "generic",
) -> str:
    """Build a concise, category-aware state contract for one Flow clip."""

    def clean_clause(value: Any) -> str:
        return str(value).strip().rstrip(". ;")

    action_items = getattr(scene_plan, "visible_micro_actions", []) or getattr(
        scene_plan, "ordered_actions", []
    )
    actions = " ".join(
        f"{index}. {clean_clause(action)}" for index, action in enumerate(action_items, 1)
    )
    start_state = clean_clause(
        getattr(scene_plan, "start_state", "the approved current scene state")
    )
    stop_state = clean_clause(
        getattr(scene_plan, "exact_stop_state", "")
        or getattr(scene_plan, "end_state", "the listed current construction state")
    )
    completion_range = getattr(scene_plan, "completion_range", "") or "current stage only"
    is_final_scene = bool(getattr(scene_plan, "is_final_scene", False))
    state_rules = {
        "architecture": (
            "Keep every already-built structural element visible and fixed; only surfaces or components named in the action sequence may change."
        ),
        "assembly": (
            "Keep every already-installed component visible, attached, and fixed in the same position; loose parts move only through visible hand or tool contact."
        ),
        "cooking": (
            "Keep every already-prepared or cooked element visible in its current state; ingredients may change only through the listed visible action."
        ),
        "craft": (
            "Keep every already-attached craft element visible and fixed; loose materials, scraps, and tools move only through visible hand contact."
        ),
        "generic": (
            "Nothing may appear, disappear, move, or transform unless caused by a listed visible action."
        ),
    }
    override_line = build_user_override_lock(user_overrides, is_final_scene)
    temporal_camera_lock = (
        "Never morph, redesign, replace, remove, reset, or rebuild the subject during motion. During all listed "
        "work and cleanup, never rescale, reframe, change camera angle, or use a cutaway shot. Only after every "
        "listed action and cleanup is complete may an explicitly listed final reveal change framing. "
        if is_final_scene
        else "Never morph, redesign, replace, remove, rescale, reframe, reset, or rebuild the subject during "
        "motion; no alternate camera angle or cutaway shot. "
    )
    base = (
        "INPUT FRAME LOCK: The uploaded frame is immutable visual ground truth. Keep subject identity, silhouette, "
        "proportions, camera, scale, lighting, workspace, and every unlisted element unchanged. "
        + override_line
        + f"START STATE: {start_state}. "
        f"CURRENT STAGE RANGE: {completion_range}; stop immediately at the end-frame contract and do not proceed beyond it. "
        f"STATE RULE: {state_rules.get(state_policy, state_rules['generic'])} "
        f"VISIBLE ACTION SEQUENCE ({len(action_items)} physically observable actions): {actions}. "
        "Perform only this sequence in order; do not invent work or begin a later stage. "
        "TEMPORAL DELTA LOCK: every frame must be the previous frame plus only the currently listed hand-driven change. "
        "Carry all completed work cumulatively through every action. "
        + temporal_camera_lock
        + f"END FRAME CONTRACT: {stop_state}. "
    )
    if is_final_scene:
        return (
            base
            + "FINAL CLEANUP: after the listed work, visibly move unused loose materials, scraps, and tools out of "
            "frame by hand. Leave only the completed subject and required environment, withdraw the hands, and hold "
            "the clean hero frame for the remaining moment."
        )
    return (
        base
        + "STAGING LOCK: all not-yet-used materials and parts remain visible, untouched, and in the same positions "
        "inside the designated edge staging tray. If the sequence finishes early, start no new work; hold the exact "
        "end frame with minimal hand withdrawal."
    )


def build_user_override_lock(
    user_overrides: dict[str, Any] | None,
    is_final_scene: bool = False,
) -> str:
    """Compile user intent into a high-priority visual contract."""
    overrides = {
        key: value for key, value in (user_overrides or {}).items() if value not in (None, "", [])
    }
    if not overrides:
        return ""

    scale_value = overrides.pop("scale", None) or overrides.pop("frame_coverage", None)
    additional = overrides.pop("additional_instructions", None)
    clauses = [f"{key}: {value}" for key, value in overrides.items()]
    if additional:
        clauses.append(f"additional instructions: {additional}")

    parts = ["USER OVERRIDE LOCK (HIGH PRIORITY):"]
    if scale_value:
        reveal_exception = (
            " Preserve that apparent size until an explicitly listed final reveal begins."
            if is_final_scene
            else " Preserve that exact apparent size and frame occupancy for the entire clip."
        )
        parts.append(f"required scale and composition: {scale_value}.{reveal_exception}")
        parts.append(
            "Do not zoom, crop, reframe, shrink, or enlarge the subject during construction."
        )
    if clauses:
        parts.append("; ".join(clauses) + ".")
    return " ".join(parts) + " "


def apply_master_prompt_overrides(
    prompt: str,
    user_overrides: dict[str, Any] | None,
) -> str:
    """Place composition overrides before the master-image description."""
    lock = build_user_override_lock(user_overrides)
    if not lock:
        return prompt.strip()
    marker = "Negative Prompt:"
    body = prompt.split(marker, 1)[0].strip()
    body_marker = "MASTER PROMPT BODY:"
    if body_marker in body:
        body = body.split(body_marker, 1)[1].strip()
    composed = (
        f"MASTER COMPOSITION CONTRACT: Establish the requested subject size and framing now; this master image "
        f"becomes the immutable scale reference for every later scene. {lock}{body_marker} {body}"
    )
    if marker not in prompt:
        return composed
    negative = prompt.rsplit(marker, 1)[1].lstrip()
    return f"{composed} {marker}{negative}"


def state_policy_for_profile(profile_id: str) -> str:
    """Map a profile to the physical state policy used after NIM rewriting."""
    if profile_id == "architecture.korean":
        return "architecture"
    if profile_id in {"vehicle.assembly", "product.assembly"}:
        return "assembly"
    if profile_id == "cooking.miniature":
        return "cooking"
    if profile_id == "home_decor.diy":
        return "craft"
    return "generic"


def append_scene_control_block(
    prompt: str,
    scene_plan: ScenePlan | Any,
    user_overrides: dict[str, Any] | None = None,
    state_policy: str = "generic",
) -> str:
    """Keep the immutable negative prompt terminal while adding shared scene controls."""
    control = build_scene_control_block(scene_plan, user_overrides, state_policy)
    marker = "Negative Prompt:"
    if marker not in prompt:
        return f"{control} PROMPT BODY: {prompt.rstrip()}"
    # A model may repeat the terminal section. Keep only its final value.
    body = prompt.split(marker, 1)[0]
    if "PROMPT BODY:" in body:
        body = body.split("PROMPT BODY:", 1)[1].strip()
    else:
        for existing_marker in (
            "INPUT FRAME LOCK:",
            "The uploaded input frame is immutable visual ground truth.",
        ):
            if existing_marker in body:
                body = body.split(existing_marker, 1)[0]
    negative = prompt.rsplit(marker, 1)[1]
    return f"{control} PROMPT BODY: {body.rstrip()} {marker}{negative.lstrip()}"


# Profile interface per Section 13.1
@dataclass
class Profile:
    profile_id: str
    version: str
    topic_label: str
    workflow_mode: WorkflowMode
    allowed_total_durations: list[int]
    default_total_duration: int
    clip_duration_seconds: int
    genre: str = ""
    subtype: str = ""
    scene_plans: list[ScenePlan] = field(default_factory=list)
    scene_plans_factory: Callable | None = None
    selection_schema: dict = field(default_factory=dict)
    style_bible_factory: Callable | None = None
    first_frame_factory: Callable | None = None
    scene_prompt_factory: Callable | None = None
    audio_contract: dict = field(default_factory=dict)
    negative_prompt_base: str = ""
    template_exclusions: list[str] = field(default_factory=list)
    workflow_mode_by_duration: dict[int, WorkflowMode] = field(default_factory=dict)

    def make_style_bible(self, topic: str, subtype: str, **kwargs) -> StyleBible:
        raise NotImplementedError

    def make_first_frame_prompt(self, topic: str, subtype: str, **kwargs) -> str:
        raise NotImplementedError

    def make_scene_video_prompt(self, scene_id: int, topic: str, subtype: str, **kwargs) -> str:
        raise NotImplementedError

    def get_selection_schema(self) -> dict:
        """Return JSON Schema for user selection validation."""
        return self.selection_schema

    def get_workflow_mode(self, duration_seconds: int) -> WorkflowMode:
        """Resolve the workflow for a duration without changing the legacy default."""
        return self.workflow_mode_by_duration.get(duration_seconds, self.workflow_mode)


# Registry
PROFILE_REGISTRY: dict[str, Profile] = {}


def register_profile(profile: Profile) -> None:
    PROFILE_REGISTRY[profile.profile_id] = profile


def get_profile(profile_id: str) -> Profile | None:
    return PROFILE_REGISTRY.get(profile_id)


def list_profiles() -> list[Profile]:
    return list(PROFILE_REGISTRY.values())


def load_all_profiles() -> None:
    """Import all profile modules to register them."""
    # Modules register themselves on import


# Convenience functions for serialization
def profile_to_dict(profile: Profile) -> dict:
    """Return manifest-safe metadata without serializing executable factories."""
    workflow_mode_by_duration = {
        str(duration): profile.get_workflow_mode(duration).value
        for duration in profile.allowed_total_durations
    }
    return {
        "profile_id": profile.profile_id,
        "version": profile.version,
        "topic_label": profile.topic_label,
        "genre": profile.genre,
        "subtype": profile.subtype,
        "workflow_mode": profile.workflow_mode.value,
        "workflow_mode_by_duration": workflow_mode_by_duration,
        "allowed_total_durations": profile.allowed_total_durations,
        "default_total_duration": profile.default_total_duration,
        "clip_duration_seconds": profile.clip_duration_seconds,
        "scene_plans": [sp.to_dict() for sp in profile.scene_plans],
        "selection_schema": profile.selection_schema,
        "scene_plans_factory": profile.scene_plans_factory is not None,
        "style_bible_factory": profile.style_bible_factory is not None,
        "first_frame_factory": profile.first_frame_factory is not None,
        "scene_prompt_factory": profile.scene_prompt_factory is not None,
        "audio_contract": profile.audio_contract,
        "negative_prompt_base": profile.negative_prompt_base,
        "template_exclusions": profile.template_exclusions,
    }


def profile_to_json(profile: Profile) -> str:
    """Serialize profile metadata to JSON for the schema registry."""
    return json.dumps(profile_to_dict(profile), ensure_ascii=False)
