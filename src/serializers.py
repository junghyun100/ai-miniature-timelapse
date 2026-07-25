"""
Canonical Serializers - Section 11.6

Implements the canonical prompt serialization format for:
- Copy Master Image Prompt
- Copy Scene Video Prompt
- Copy Full Scene
- Copy All (full plan)
- Source Revision computation (Section 14.1)

All serializations must be deterministic and match between Python and browser.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .domain import (
    Project,
    Scene,
    AssetRef,
    AssetKind,
    AssetScope,
    WorkflowMode,
    AspectRatio,
    ProvenanceSource,
    ProfileId,
    ScenePlan,
    StyleBible,
)


# Immutable negative prompt line (shared across all profiles per Section 11.6)
IMMUTABLE_NEGATIVE = (
    "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, "
    "bad anatomy, deformed hands, blurry, miniature people, small people, "
    "tiny workers, human figures"
)


# ============================================================================
# Internal Helpers
# ============================================================================

def _nfc_normalize(obj: Any) -> Any:
    """Recursively normalize all strings to NFC Unicode form."""
    if isinstance(obj, str):
        return unicodedata.normalize("NFC", obj)
    elif isinstance(obj, dict):
        return {_nfc_normalize(k): _nfc_normalize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_nfc_normalize(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_nfc_normalize(item) for item in obj)
    return obj


def _canonical_json(obj: Any) -> str:
    """
    Serialize to JSON with:
    - Recursively sorted keys
    - No insignificant whitespace
    - Stable array order
    - NFC normalization
    """
    normalized = _nfc_normalize(obj)
    return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _style_bible_to_dict(sb: StyleBible) -> dict[str, Any]:
    """Convert StyleBible to dict for serialization."""
    return {
        "identity_lock": sb.identity_lock,
        "materials": sb.materials,
        "camera": sb.camera,
        "lighting": sb.lighting,
        "color_palette": sb.color_palette,
        "workspace": sb.workspace,
        "hands_rule": sb.hands_rule,
        "motion_rule": sb.motion_rule,
    }


def _serialize_asset_ref(asset: Optional[AssetRef]) -> str:
    """
    Serialize AssetRef to the canonical instruction format.
    Per Section 9.4 and 11.6.
    """
    if not asset:
        return "none"

    parts = [asset.logical_id]
    if asset.kind:
        parts.append(f"kind={asset.kind.value}")
    if asset.scope:
        parts.append(f"scope={asset.scope.value}")
    if asset.flow_asset_label:
        parts.append(f"label={asset.flow_asset_label}")
    if asset.local_path:
        parts.append(f"local={asset.local_path}")
    if asset.source_scene_id is not None:
        parts.append(f"source_scene={asset.source_scene_id}")

    return " | ".join(parts)


def _serialize_project_header(project: Project, provenance: Optional[ProvenanceSource] = None) -> list[str]:
    """Serialize the project header section per Section 11.6."""
    lines = [
        f"Project: {project.topic}",
        f"Topic Label: {project.topic_label}",
        f"Profile: {project.profile_id}@{project.profile_version}",
        f"Workflow: {project.workflow_mode.value}",
        f"Duration: {project.duration_seconds}s ({project.scene_count} scene{'s' if project.scene_count != 1 else ''} × {project.clip_duration_seconds}s)",
        f"Aspect Ratio: {project.aspect_ratio.value}",
        f"Source: {provenance.value if provenance else 'local'}",
        f"Source Revision: {project.source_revision}",
    ]
    return lines


def _serialize_master_image(scene: Scene) -> list[str]:
    """Serialize MASTER IMAGE section (Scene 1 only) per Section 11.6."""
    return [
        "MASTER IMAGE",
        f"First Frame Prompt: {scene.first_frame_prompt}",
        f"Template Exclusions: {scene.template_exclusions}",
        f"Negative Prompt: {IMMUTABLE_NEGATIVE}",
    ]


def _serialize_scene(scene: Scene, scene_index: int) -> list[str]:
    """Serialize a single SCENE N block per Section 11.6."""
    lines = [f"SCENE {scene_index} — {scene.name}"]
    lines.append(f"Input: {_serialize_asset_ref(scene.asset_ref)}")
    lines.append(f"Video Prompt: {scene.video_prompt}")
    lines.append(f"Template Exclusions: {scene.template_exclusions}")
    lines.append(f"Negative Prompt: {IMMUTABLE_NEGATIVE}")
    return lines


# ============================================================================
# Public API
# ============================================================================

def compute_source_revision(project: Project) -> str:
    """
    Compute SHA-256 source revision from canonical JSON of prompt-affecting fields.

    Per Section 14.1, includes:
    - profile_id, profile_version, workflow_mode
    - topic, genre, subtype, topic_label
    - model_name, dish_name, craft_name
    - duration_seconds, clip_duration_seconds, aspect_ratio
    - style_bible
    - derived_fields (profile-specific)
    - scene_plans (start_state, ordered_actions, end_state, forbidden_changes per scene)
    - narration, idea_seed
    - flow_execution_profile_id
    - nim_enabled, nim_model_id, nim_refinement_policy

    Excludes transient values: API keys, UI state, timestamps, loading status,
    selected scene tab, copied/not-copied state.

    Args:
        project: Project to compute revision for

    Returns:
        SHA-256 hex digest prefixed with "sha256:"
    """
    # Build the included object per Section 14.1
    included: dict[str, Any] = {
        "profile_id": project.profile_id,
        "profile_version": project.profile_version,
        "workflow_mode": project.workflow_mode.value,
        "topic": project.topic,
        "genre": project.genre,
        "subtype": project.subtype,
        "topic_label": project.topic_label,
        "model_name": project.model_name,
        "dish_name": project.dish_name,
        "craft_name": project.craft_name,
        "duration_seconds": project.duration_seconds,
        "clip_duration_seconds": project.clip_duration_seconds,
        "aspect_ratio": project.aspect_ratio.value,
        "style_bible": _style_bible_to_dict(project.style_bible),
        "derived_fields": project.derived_fields,
        "scene_plans": [
            {
                "scene_id": sp.scene_id,
                "name": sp.name,
                "start_state": sp.start_state,
                "ordered_actions": sp.ordered_actions,
                "end_state": sp.end_state,
                "forbidden_changes": sp.forbidden_changes.value,
                "input_mode": sp.input_mode.value,
            }
            for sp in project.scene_plans
        ],
        "narration": project.narration,
        "idea_seed": project.idea_seed,
        "flow_execution_profile_id": project.flow_execution_profile_id,
        "nim_enabled": project.nim_enabled,
        "nim_model_id": project.nim_model_id,
        "nim_refinement_policy": project.nim_refinement_policy,
    }

    canonical = _canonical_json(included)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def serialize_full_plan(project: Project) -> str:
    """
    Serialize the complete canonical plan per Section 11.6.

    Field order:
    1. Project header
    2. MASTER IMAGE (Scene 1 only)
    3. SCENE 1 block
    4. SCENE 2..N blocks (no First Frame Prompt)

    In single-clip mode there is only Scene 1.

    Args:
        project: Project to serialize

    Returns:
        Canonical string representation
    """
    lines = []

    # Project header
    lines.extend(_serialize_project_header(project, project.provenance.source if project.provenance else None))
    lines.append("")  # blank line after header

    # MASTER IMAGE (Scene 1 only)
    if project.scenes:
        scene1 = project.scenes[0]
        lines.extend(_serialize_master_image(scene1))
        lines.append("")  # blank line after MASTER IMAGE

    # SCENE blocks
    for i, scene in enumerate(project.scenes, 1):
        lines.extend(_serialize_scene(scene, i))
        if i < len(project.scenes):
            lines.append("")  # blank line between scenes

    return "\n".join(lines)


def serialize_master_image_prompt(project: Project) -> str:
    """
    Serialize MASTER IMAGE section for Copy Master Image Prompt action.

    Includes: first-frame prompt, template exclusions, immutable negative line.
    Per Section 11.6 / 11.6 special copy actions.
    """
    if not project.scenes:
        return ""

    scene1 = project.scenes[0]
    lines = _serialize_master_image(scene1)
    return "\n".join(lines)


def serialize_scene_video_prompt(project: Project, scene_id: int) -> str:
    """
    Serialize SCENE N block for Copy Scene Video Prompt action.

    Includes: video prompt, template exclusions, immutable negative line.
    Per Section 11.6 special copy actions.
    """
    scene = next((s for s in project.scenes if s.id == scene_id), None)
    if not scene:
        return ""

    lines = [
        f"SCENE {scene_id} — {scene.name}",
        f"Video Prompt: {scene.video_prompt}",
        f"Template Exclusions: {scene.template_exclusions}",
        f"Negative Prompt: {IMMUTABLE_NEGATIVE}",
    ]
    return "\n".join(lines)


def serialize_full_scene(project: Project, scene_id: int) -> str:
    """
    Serialize the exact visible SCENE N block for Copy Full Scene action.

    Per Section 11.6 special copy actions.
    """
    scene = next((s for s in project.scenes if s.id == scene_id), None)
    if not scene:
        return ""

    if scene_id == 1:
        lines = [
            "MASTER IMAGE",
            f"First Frame Prompt: {scene.first_frame_prompt}",
            f"Template Exclusions: {scene.template_exclusions}",
            f"Negative Prompt: {IMMUTABLE_NEGATIVE}",
            "",
            f"SCENE 1 — {scene.name}",
        ]
    else:
        lines = [f"SCENE {scene_id} — {scene.name}"]

    lines.append(f"Input: {_serialize_asset_ref(scene.asset_ref)}")
    lines.append(f"Video Prompt: {scene.video_prompt}")
    lines.append(f"Template Exclusions: {scene.template_exclusions}")
    lines.append(f"Negative Prompt: {IMMUTABLE_NEGATIVE}")

    return "\n".join(lines)


# ============================================================================
# Copy Action Results
# ============================================================================

@dataclass
class CopyActionResult:
    """Result of a copy action with metadata."""
    action: str
    scene_id: Optional[int]
    text: str
    source_revision: str
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "scene_id": self.scene_id,
            "text": self.text,
            "source_revision": self.source_revision,
            "timestamp": self.timestamp,
        }


def perform_copy_action(
    project: Project,
    action: str,
    scene_id: Optional[int] = None,
) -> CopyActionResult:
    """
    Perform a specialized copy action per Section 11.6.

    Actions:
    - "master_image": Copy Master Image Prompt (first-frame prompt, exclusions, negative)
    - "scene_video": Copy Scene Video Prompt (video prompt, exclusions, negative for given scene)
    - "full_scene": Copy Full Scene (exact visible scene block)
    - "all": Copy All (full canonical plan)

    Args:
        project: Current project
        action: Copy action type
        scene_id: Required for scene_video and full_scene actions (1-based)

    Returns:
        CopyActionResult with serialized text and metadata

    Raises:
        ValueError: If action is unknown or scene_id required but not provided
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    source_revision = project.source_revision

    if action == "master_image":
        if not project.scenes:
            raise ValueError("No scenes in project")
        scene1 = project.scenes[0]
        lines = _serialize_master_image(scene1)
        text = "\n".join(lines)
        return CopyActionResult(
            action="master_image",
            scene_id=1,
            text=text,
            source_revision=source_revision,
            timestamp=timestamp,
        )

    elif action == "scene_video":
        if scene_id is None:
            raise ValueError("scene_id required for scene_video action")
        if scene_id < 1 or scene_id > len(project.scenes):
            raise ValueError(f"Invalid scene_id: {scene_id}. Project has {len(project.scenes)} scenes.")
        scene = project.scenes[scene_id - 1]
        lines = [
            f"SCENE {scene_id} — {scene.name}",
            f"Video Prompt: {scene.video_prompt}",
            f"Template Exclusions: {scene.template_exclusions}",
            f"Negative Prompt: {IMMUTABLE_NEGATIVE}",
        ]
        text = "\n".join(lines)
        return CopyActionResult(
            action="scene_video",
            scene_id=scene_id,
            text=text,
            source_revision=source_revision,
            timestamp=timestamp,
        )

    elif action == "full_scene":
        if scene_id is None:
            raise ValueError("scene_id required for full_scene action")
        if scene_id < 1 or scene_id > len(project.scenes):
            raise ValueError(f"Invalid scene_id: {scene_id}. Project has {len(project.scenes)} scenes.")
        scene = project.scenes[scene_id - 1]

        if scene_id == 1:
            # Scene 1 includes MASTER IMAGE
            lines = []
            lines.extend(_serialize_master_image(scene))
            lines.append("")
            lines.extend(_serialize_scene(scene, 1))
        else:
            # Scenes 2+ only the SCENE block (no MASTER IMAGE, no First Frame Prompt)
            lines = _serialize_scene(scene, scene_id)

        text = "\n".join(lines)
        return CopyActionResult(
            action="full_scene",
            scene_id=scene_id,
            text=text,
            source_revision=source_revision,
            timestamp=timestamp,
        )

    elif action == "all":
        text = serialize_full_plan(project)
        return CopyActionResult(
            action="all",
            scene_id=None,
            text=text,
            source_revision=source_revision,
            timestamp=timestamp,
        )

    else:
        raise ValueError(f"Unknown copy action: {action}")


# ============================================================================
# Export all public symbols
# ============================================================================

__all__ = [
    "IMMUTABLE_NEGATIVE",
    "compute_source_revision",
    "serialize_full_plan",
    "serialize_master_image_prompt",
    "serialize_scene_video_prompt",
    "serialize_full_scene",
    "perform_copy_action",
    "CopyActionResult",
    "_canonical_json",
    "_serialize_asset_ref",
]