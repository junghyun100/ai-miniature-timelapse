"""
Canonical Domain Models for AI Miniature Timelapse v2.0

This module defines the authoritative Python data structures that correspond
to the JSON schemas in schema/. All serialization, validation, and source
revision computation must go through these models.

Key Invariants (Section 7):
- Scene 1 MUST have first_frame_prompt; Scenes 2+ MUST NOT
- Relay profiles: Scene N+1 input_mode == PREVIOUS_FINAL_FRAME until Scene N confirmed
- StyleBible.identity_lock MUST appear verbatim in every prompt
- Source revision SHA-256 covers exactly the included fields (NFC, sorted keys)
- NIM request/response request_id/source_revision MUST match exactly
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
import uuid
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any


class WorkflowMode(StrEnum):
    REFERENCE_FRAME_RELAY = "REFERENCE_FRAME_RELAY"
    SINGLE_CLIP_FROM_MASTER = "SINGLE_CLIP_FROM_MASTER"


class ProfileId(StrEnum):
    ARCHITECTURE_KOREAN = "architecture.korean"
    VEHICLE_ASSEMBLY = "vehicle.assembly"
    HOME_DECOR_DIY = "home_decor.diy"
    COOKING_MINIATURE = "cooking.miniature"


class Genre(StrEnum):
    ARCHITECTURE = "architecture"
    VEHICLE = "vehicle"
    HOME_DECOR = "home_decor"
    COOKING = "cooking"


class AspectRatio(StrEnum):
    RATIO_9_16 = "9:16"
    RATIO_16_9 = "16:9"
    RATIO_1_1 = "1:1"


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


class NimRefinementPolicy(StrEnum):
    MUTABLE_ONLY = "mutable_only"
    ALL = "all"


class ProvenanceSource(StrEnum):
    LOCAL_PLANNER = "local_planner"
    NIM = "nim"
    FALLBACK = "fallback"
    NIM_PARTIAL_FALLBACK = "nim_partial_fallback"


class AssetKind(StrEnum):
    IMAGE = "image"
    VIDEO = "video"


class AssetScope(StrEnum):
    PROJECT = "project"
    SCENE = "scene"


# ============================================================================
# Helper Functions
# ============================================================================


def _normalize_unicode(s: str) -> str:
    """Normalize Unicode to NFC form."""
    return unicodedata.normalize("NFC", s)


def _sort_keys_recursive(obj: Any) -> Any:
    """Recursively sort dictionary keys for canonical serialization."""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: _sort_keys_recursive(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_sort_keys_recursive(item) for item in obj]
    if isinstance(obj, str):
        return _normalize_unicode(obj)
    return obj


def _canonical_json(obj: Any) -> str:
    """Serialize to canonical JSON: sorted keys, no whitespace, NFC normalized."""
    normalized = _sort_keys_recursive(obj)
    return json.dumps(normalized, separators=(",", ":"), ensure_ascii=False)


def compute_source_revision(source_draft: dict[str, Any]) -> str:
    """
    Compute SHA-256 source revision per Section 14.1.

    Included fields (exact keys from source draft):
    - profile_id, profile_version, workflow_mode
    - topic, genre, subtype, topic_label
    - model_name, dish_name, craft_name
    - duration_seconds, clip_duration_seconds, aspect_ratio
    - style_bible (full object)
    - derived_fields (full object)
    - scene_plans (full array with start_state, ordered_actions, end_state, forbidden_changes)
    - narration, idea_seed
    - flow_execution_profile_id
    - nim_enabled, nim_model_id, nim_refinement_policy

    Excluded (transient):
    - provenance, relay_branch, source_revision, schema_version
    """
    included_keys = {
        "profile_id",
        "profile_version",
        "workflow_mode",
        "topic",
        "genre",
        "subtype",
        "topic_label",
        "selection",
        "subject",
        "category",
        "model_name",
        "dish_name",
        "dish_key",
        "craft_name",
        "idea_name",
        "materials",
        "final_object",
        "korean_narration",
        "user_overrides",
        "duration_seconds",
        "clip_duration_seconds",
        "aspect_ratio",
        "style_bible",
        "derived_fields",
        "scene_plans",
        "narration",
        "idea_seed",
        "flow_execution_profile_id",
        "nim_enabled",
        "nim_model_id",
        "nim_refinement_policy",
    }

    # Extract only included fields
    filtered = {k: v for k, v in source_draft.items() if k in included_keys}

    # Canonical serialization
    canonical = _canonical_json(filtered)

    # SHA-256
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def serialize_canonical(obj: Any) -> str:
    """Serialize any dataclass or dict to canonical JSON string."""
    if is_dataclass(obj):
        obj = asdict(obj)
    return _canonical_json(obj)


def validate_invariants(project: Project) -> list[str]:
    """
    Validate all Section 7 invariants.
    Returns list of error messages (empty = valid).
    """
    errors = []
    from .profile_types import PROFILE_REGISTRY

    # Invariant: Scene 1 MUST have first_frame_prompt; Scenes 2+ MUST NOT
    if project.scenes:
        scene1 = project.scenes[0]
        if scene1.first_frame_prompt is None or scene1.first_frame_prompt == "":
            errors.append("Scene 1 must have non-empty first_frame_prompt")
        for i, scene in enumerate(project.scenes[1:], start=2):
            if scene.first_frame_prompt is not None and scene.first_frame_prompt != "":
                errors.append(f"Scene {i} must not have first_frame_prompt (relay mode)")

    # Invariant: Relay profiles require PREVIOUS_FINAL_FRAME input mode
    if project.workflow_mode == WorkflowMode.REFERENCE_FRAME_RELAY:
        for i, scene in enumerate(project.scenes):
            if i == 0:
                if scene.input_mode != InputMode.MASTER_IMAGE:
                    errors.append("Scene 1 must have MASTER_IMAGE input_mode in relay mode")
            else:
                if scene.input_mode != InputMode.PREVIOUS_FINAL_FRAME:
                    errors.append(
                        f"Scene {i + 1} must have PREVIOUS_FINAL_FRAME input_mode in relay mode"
                    )

    # Invariant: StyleBible.identity_lock must appear in every prompt
    identity_lock = project.style_bible.identity_lock
    for scene in project.scenes:
        if identity_lock not in scene.video_prompt:
            errors.append(f"Scene {scene.id}: identity_lock missing from video_prompt")
        if scene.first_frame_prompt and identity_lock not in scene.first_frame_prompt:
            errors.append(f"Scene {scene.id}: identity_lock missing from first_frame_prompt")

    # Invariant: clip_duration_seconds matches profile
    profile = PROFILE_REGISTRY.get(project.profile_id)
    if profile:
        for scene in project.scenes:
            if scene.clip_duration_seconds != profile.clip_duration_seconds:
                errors.append(
                    f"Scene {scene.id}: clip_duration_seconds {scene.clip_duration_seconds} != profile {profile.clip_duration_seconds}"
                )

    # Invariant: source_revision format
    if not project.source_revision.startswith("sha256:") or len(project.source_revision) != 71:
        errors.append(f"Invalid source_revision format: {project.source_revision}")

    return errors


# ============================================================================
# Domain Models
# ============================================================================


@dataclass
class StyleBible:
    identity_lock: str
    materials: dict[str, list[str]]  # primary, secondary, tools
    camera: dict[str, str]  # lens, angle, movement, distance
    lighting: dict[str, str]  # key, fill, mood, consistency
    color_palette: list[str]
    workspace: str
    hands_rule: str
    motion_rule: str

    def to_dict(self) -> dict:
        return asdict(self)

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
        d = asdict(self)
        # Convert enums and datetime
        d["kind"] = self.kind.value
        d["scope"] = self.scope.value
        if self.confirmed_at:
            d["confirmed_at"] = self.confirmed_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> AssetRef:
        data = data.copy()
        data["kind"] = AssetKind(data["kind"])
        data["scope"] = AssetScope(data["scope"])
        if data.get("confirmed_at"):
            data["confirmed_at"] = datetime.fromisoformat(data["confirmed_at"])
        return cls(**data)


@dataclass
class FlowExecutionProfile:
    id: str
    display_name: str
    provider: str
    model_label: str
    supports_start_frame: bool
    supported_clip_durations_seconds: list[int]
    supports_prompt_audio: bool
    last_verified_at: datetime
    verification_url: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["last_verified_at"] = self.last_verified_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> FlowExecutionProfile:
        data = data.copy()
        data["last_verified_at"] = datetime.fromisoformat(data["last_verified_at"])
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

    def to_dict(self) -> dict:
        d = asdict(self)
        d["input_mode"] = self.input_mode.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> ScenePlan:
        data = data.copy()
        data["input_mode"] = InputMode(data["input_mode"])
        return cls(**data)


@dataclass
class Scene:
    id: int
    name: str
    input_mode: InputMode
    asset_ref: AssetRef
    first_frame_prompt: str | None  # Scene 1 only; None for Scenes 2+
    video_prompt: str
    template_exclusions: str
    negative_prompt: str
    clip_duration_seconds: int
    lineage_revision: str
    status: SceneStatus = SceneStatus.LOCKED
    confirmed_at: datetime | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["input_mode"] = self.input_mode.value
        d["asset_ref"] = self.asset_ref.to_dict()
        d["status"] = self.status.value
        if self.confirmed_at:
            d["confirmed_at"] = self.confirmed_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Scene:
        data = data.copy()
        data["input_mode"] = InputMode(data["input_mode"])
        data["asset_ref"] = AssetRef.from_dict(data["asset_ref"])
        data["status"] = SceneStatus(data["status"])
        if data.get("confirmed_at"):
            data["confirmed_at"] = datetime.fromisoformat(data["confirmed_at"])
        return cls(**data)


@dataclass
class RelayBranch:
    branch_id: str
    parent_branch_id: str | None
    scene_statuses: dict[str, SceneStatus]  # scene_id (str) -> status
    asset_refs: list[AssetRef]
    created_at: datetime
    lineage_revision: str
    nonce: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["scene_statuses"] = {k: v.value for k, v in self.scene_statuses.items()}
        d["asset_refs"] = [ar.to_dict() for ar in self.asset_refs]
        d["created_at"] = self.created_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> RelayBranch:
        data = data.copy()
        data["scene_statuses"] = {k: SceneStatus(v) for k, v in data["scene_statuses"].items()}
        data["asset_refs"] = [AssetRef.from_dict(ar) for ar in data["asset_refs"]]
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class Provenance:
    source: ProvenanceSource
    provider: str
    model_id: str
    base_url_label: str
    generated_at: datetime
    request_id: str
    source_revision: str
    fallback_scene_ids: list[int] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["source"] = self.source.value
        d["generated_at"] = self.generated_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Provenance:
        data = data.copy()
        data["source"] = ProvenanceSource(data["source"])
        data["generated_at"] = datetime.fromisoformat(data["generated_at"])
        return cls(**data)


@dataclass
class SourceRevision:
    algorithm: str = "sha256"
    included_fields: list[str] = field(default_factory=list)
    excluded_fields: list[str] = field(default_factory=list)
    hash: str = ""
    canonical_json: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================================
# Main Project Model
# ============================================================================


@dataclass
class Project:
    schema_version: str = "2.0"
    topic: str = ""
    topic_label: str = ""
    genre: str | None = None
    subtype: str | None = None
    model_name: str | None = None
    dish_name: str | None = None
    craft_name: str | None = None
    profile_id: str = ""
    profile_version: str = ""
    workflow_mode: WorkflowMode = WorkflowMode.SINGLE_CLIP_FROM_MASTER
    duration_seconds: int = 30
    clip_duration_seconds: int = 10
    aspect_ratio: AspectRatio = AspectRatio.RATIO_9_16
    style_bible: StyleBible | None = None
    derived_fields: dict = field(default_factory=dict)
    scene_plans: list[ScenePlan] = field(default_factory=list)
    scene_count: int = 0
    source_revision: str = ""
    flow_execution_profile_id: str = ""
    nim_enabled: bool = False
    nim_model_id: str = ""
    nim_refinement_policy: NimRefinementPolicy = NimRefinementPolicy.MUTABLE_ONLY
    narration: str | None = None
    idea_seed: str | None = None
    user_overrides: dict[str, Any] = field(default_factory=dict)
    provenance: Provenance | None = None
    relay_branch: RelayBranch | None = None
    scenes: list[Scene] = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.workflow_mode, str):
            self.workflow_mode = WorkflowMode(self.workflow_mode)
        if isinstance(self.style_bible, dict):
            self.style_bible = StyleBible.from_dict(self.style_bible)

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage."""
        d = asdict(self)
        d["workflow_mode"] = self.workflow_mode.value
        d["aspect_ratio"] = (
            self.aspect_ratio.value
            if isinstance(self.aspect_ratio, AspectRatio)
            else self.aspect_ratio
        )
        d["provenance"] = self.provenance.to_dict() if self.provenance else None
        d["relay_branch"] = self.relay_branch.to_dict() if self.relay_branch else None
        d["style_bible"] = self.style_bible.to_dict() if self.style_bible else None
        d["scene_plans"] = [sp.to_dict() for sp in self.scene_plans]
        d["scenes"] = [s.to_dict() for s in self.scenes]
        if isinstance(self.nim_refinement_policy, NimRefinementPolicy):
            d["nim_refinement_policy"] = self.nim_refinement_policy.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Project:
        data = data.copy()
        data["workflow_mode"] = WorkflowMode(data["workflow_mode"])
        if data.get("aspect_ratio"):
            data["aspect_ratio"] = AspectRatio(data["aspect_ratio"])
        if data.get("style_bible"):
            data["style_bible"] = StyleBible.from_dict(data["style_bible"])
        if data.get("scene_plans"):
            data["scene_plans"] = [ScenePlan.from_dict(sp) for sp in data["scene_plans"]]
        if data.get("scenes"):
            data["scenes"] = [Scene.from_dict(s) for s in data["scenes"]]
        if data.get("provenance"):
            data["provenance"] = Provenance.from_dict(data["provenance"])
        if data.get("relay_branch"):
            data["relay_branch"] = RelayBranch.from_dict(data["relay_branch"])
        if data.get("nim_refinement_policy"):
            data["nim_refinement_policy"] = NimRefinementPolicy(data["nim_refinement_policy"])
        return cls(**data)

    def compute_source_revision(self) -> str:
        """Compute and return source revision for current state."""
        source_draft = {
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "workflow_mode": self.workflow_mode.value,
            "topic": self.topic,
            "genre": self.genre,
            "subtype": self.subtype,
            "topic_label": self.topic_label,
            "model_name": self.model_name,
            "dish_name": self.dish_name,
            "craft_name": self.craft_name,
            "duration_seconds": self.duration_seconds,
            "clip_duration_seconds": self.clip_duration_seconds,
            "aspect_ratio": (
                self.aspect_ratio.value
                if isinstance(self.aspect_ratio, AspectRatio)
                else self.aspect_ratio
            ),
            "style_bible": self.style_bible.to_dict() if self.style_bible else {},
            "derived_fields": self.derived_fields,
            "scene_plans": [sp.to_dict() for sp in self.scene_plans],
            "narration": self.narration,
            "idea_seed": self.idea_seed,
            "user_overrides": self.user_overrides,
            "flow_execution_profile_id": self.flow_execution_profile_id,
            "nim_enabled": self.nim_enabled,
            "nim_model_id": self.nim_model_id,
            "nim_refinement_policy": (
                self.nim_refinement_policy.value
                if isinstance(self.nim_refinement_policy, NimRefinementPolicy)
                else self.nim_refinement_policy
            ),
        }
        return compute_source_revision(source_draft)

    def validate(self) -> list[str]:
        """Validate all invariants. Returns list of errors."""
        return validate_invariants(self)


# ============================================================================
# NIM Contract Models
# ============================================================================


@dataclass
class NimSceneRequest:
    id: int
    name: str
    start_state: str
    ordered_actions: list[str]
    end_state: str
    local_first_frame_prompt: str
    local_video_prompt: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NimSceneResponse:
    id: int
    first_frame_prompt: str
    video_prompt: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NimRequest:
    schema_version: str = "2.0"
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_revision: str = ""
    profile: dict = field(default_factory=dict)
    subject: dict = field(default_factory=dict)
    style_bible: dict = field(default_factory=dict)
    scenes: list[NimSceneRequest] = field(default_factory=list)
    mutable_fields: list[str] = field(
        default_factory=lambda: ["scenes.*.first_frame_prompt", "scenes.*.video_prompt"]
    )
    immutable_rules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["scenes"] = [s.to_dict() for s in self.scenes]
        return d


@dataclass
class NimResponse:
    schema_version: str = "2.0"
    request_id: str = ""
    source_revision: str = ""
    scenes: list[NimSceneResponse] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["scenes"] = [s.to_dict() for s in self.scenes]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> NimResponse:
        data = data.copy()
        data["scenes"] = [NimSceneResponse(**s) for s in data["scenes"]]
        return cls(**data)


def normalize_nim_response(
    response: NimResponse, local_plans: list[NimSceneRequest], source_revision: str
) -> tuple[NimResponse, list[str]]:
    """
    Post-NIM normalization per Section 14.5.

    Rules:
    - If response.source_revision != source_revision -> STALE, entire response discarded
    - If response.request_id != request.request_id -> mismatch, discarded
    - Scene count must match exactly
    - Scene N first_frame_prompt must be empty for N>=2 (relay mode)
    - Video prompt must not be empty
    - Negative prompt must not be altered (local negative_prompt_base preserved)
    - Identity lock must be present in all video_prompts
    - Wrong subtype/dish/model in response -> error (no fallback)

    Returns (normalized_response, warnings)
    Raises ValueError on validation failures (no fallback to local templates)
    """
    warnings = []

    # Check staleness
    if response.source_revision != source_revision:
        raise ValueError(
            f"Stale NIM response: source_revision mismatch (response={response.source_revision}, expected={source_revision})"
        )

    # Validate scene count - MUST match exactly, no padding with fallbacks
    if len(response.scenes) != len(local_plans):
        raise ValueError(
            f"NIM response scene count mismatch: expected {len(local_plans)}, got {len(response.scenes)}. No fallback available - NIM must return correct number of scenes."
        )

    # Per-scene validation - NO FALLBACK to local templates
    for i, (nim_scene, local_scene) in enumerate(zip(response.scenes, local_plans, strict=False)):
        # Scene ID must match
        if nim_scene.id != local_scene.id:
            raise ValueError(
                f"Scene {i + 1}: ID mismatch (expected {local_scene.id}, got {nim_scene.id}). NIM response is invalid."
            )

        # Scene 2+ first_frame_prompt must be empty in relay mode
        if i >= 1 and nim_scene.first_frame_prompt:
            warnings.append(
                f"Scene {i + 1}: first frame prompt must be empty in relay mode, clearing"
            )
            nim_scene.first_frame_prompt = ""

        # Video prompt must not be empty - FAIL if NIM doesn't provide one
        if not nim_scene.video_prompt or not nim_scene.video_prompt.strip():
            raise ValueError(
                f"Scene {i + 1}: NIM returned empty video_prompt. No fallback to local templates - NIM must generate valid prompts."
            )

    return response, warnings
