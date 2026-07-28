"""
Profile Types - Profile Registry and Interface Definitions

Per Section 13.1 of the Reference-Frame Relay Specification v2.0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
import json


class WorkflowMode(str, Enum):
    REFERENCE_FRAME_RELAY = "REFERENCE_FRAME_RELAY"
    SINGLE_CLIP_FROM_MASTER = "SINGLE_CLIP_FROM_MASTER"


class AspectRatio(str, Enum):
    RATIO_9_16 = "9:16"
    RATIO_16_9 = "16:9"
    RATIO_1_1 = "1:1"


class NimRefinementPolicy(str, Enum):
    MUTABLE_ONLY = "mutable_only"
    ALL = "all"


class ProvenanceSource(str, Enum):
    LOCAL_PLANNER = "local_planner"
    NVIDIA_NIM = "nvidia_nim"


class InputMode(str, Enum):
    MASTER_IMAGE = "MASTER_IMAGE"
    PREVIOUS_FINAL_FRAME = "PREVIOUS_FINAL_FRAME"
    NONE = "NONE"


class SceneStatus(str, Enum):
    LOCKED = "LOCKED"
    AWAITING_MASTER_IMAGE = "AWAITING_MASTER_IMAGE"
    AWAITING_PREVIOUS_FRAME = "AWAITING_PREVIOUS_FRAME"
    VIDEO_READY = "VIDEO_READY"
    CONFIRMED = "CONFIRMED"
    COMPLETE = "COMPLETE"
    NEEDS_RETRY = "NEEDS_RETRY"
    STALE = "STALE"


class AssetKind(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


class AssetScope(str, Enum):
    PROJECT = "project"
    SCENE = "scene"


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
    flow_asset_id: Optional[str] = None
    flow_asset_label: Optional[str] = None
    local_path: Optional[str] = None
    source_scene_id: Optional[int] = None
    confirmed_by_user: bool = False
    confirmed_at: Optional[datetime] = None
    content_hash: Optional[str] = None
    lineage_revision: Optional[str] = None

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

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items()}
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
    scene_plans_factory: Optional[Callable] = None
    selection_schema: dict = field(default_factory=dict)
    style_bible_factory: Optional[Callable] = None
    first_frame_factory: Optional[Callable] = None
    scene_prompt_factory: Optional[Callable] = None
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


def get_profile(profile_id: str) -> Optional[Profile]:
    return PROFILE_REGISTRY.get(profile_id)


def list_profiles() -> list[Profile]:
    return list(PROFILE_REGISTRY.values())


def load_all_profiles() -> None:
    """Import all profile modules to register them."""
    from .profiles import architecture, vehicle, product, home_decor, cooking
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
