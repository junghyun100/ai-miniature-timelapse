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

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .domain import (
        AssetRef,
        Project,
        ProvenanceSource,
        Scene,
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
    if isinstance(obj, dict):
        return {_nfc_normalize(k): _nfc_normalize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_nfc_normalize(item) for item in obj]
    if isinstance(obj, tuple):
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


def _serialize_asset_ref(asset: AssetRef | None) -> str:
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


def _serialize_project_header(
    project: Project, provenance: ProvenanceSource | None = None
) -> list[str]:
    """Serialize the project header section per Section 11.6."""
    return [
        f"Project: {project.topic}",
        f"Topic Label: {project.topic_label}",
        f"Profile: {project.profile_id}@{project.profile_version}",
        f"Workflow: {project.workflow_mode.value}",
        f"Duration: {project.duration_seconds}s ({project.scene_count} scene{'s' if project.scene_count != 1 else ''} × {project.clip_duration_seconds}s)",
        f"Aspect Ratio: {project.aspect_ratio.value}",
        f"Source: {provenance.value if provenance else 'local'}",
        f"Source Revision: {project.source_revision}",
    ]


def split_prompt_negative(
    prompt: str, fallback_negative: str = IMMUTABLE_NEGATIVE
) -> tuple[str, str]:
    """Split prompt into main prompt body and negative prompt if embedded, else use fallback."""
    raw_prompt = str(prompt or "").strip()
    match = re.search(
        r"\s*Negative Prompt:\s*[\"“]?([\s\S]*?)[\"”]?\s*$", raw_prompt, re.IGNORECASE
    )
    if match:
        body = raw_prompt[: match.start()].strip()
        extracted = match.group(1).strip()
    else:
        body = raw_prompt
        extracted = str(fallback_negative or IMMUTABLE_NEGATIVE).strip()

    negative = re.sub(r'^["“]+|["”]+$', "", extracted)
    negative = re.sub(r"\.+$", "", negative).strip()
    return body, negative


def _get_scene_input_label(scene_index: int, input_mode: Any | None = None) -> str:
    """Get human readable scene input label matching JS getSceneInputLabel."""
    mode_val = input_mode.value if hasattr(input_mode, "value") else str(input_mode or "")
    if scene_index <= 1 or mode_val == "MASTER_IMAGE":
        return "Master Image"
    return f"Scene {scene_index - 1} Final Frame"


def _serialize_master_image(scene: Scene) -> list[str]:
    """Serialize MASTER IMAGE section (Scene 1 only) per Section 11.6."""
    fallback = (
        getattr(scene, "negative_prompt_base", None)
        or getattr(scene, "negative_prompt", None)
        or IMMUTABLE_NEGATIVE
    )
    body, negative = split_prompt_negative(scene.first_frame_prompt, fallback)
    return [
        "MASTER IMAGE",
        f"First Frame Prompt: {body}",
        f"Template Exclusions: {scene.template_exclusions}",
        f"Negative Prompt: {negative}.",
    ]


def _serialize_scene(scene: Scene, scene_index: int) -> list[str]:
    """Serialize a single SCENE N block per Section 11.6."""
    fallback = (
        getattr(scene, "negative_prompt_base", None)
        or getattr(scene, "negative_prompt", None)
        or IMMUTABLE_NEGATIVE
    )
    body, negative = split_prompt_negative(scene.video_prompt, fallback)
    input_label = _get_scene_input_label(scene_index, scene.input_mode)
    output_ref = _serialize_asset_ref(scene.asset_ref)
    return [
        f"SCENE {scene_index} — {scene.name}",
        f"Input: {input_label}",
        f"Output: {output_ref}",
        f"Video Prompt: {body}",
        f"Template Exclusions: {scene.template_exclusions}",
        f"Negative Prompt: {negative}.",
    ]


# ============================================================================
# Public API
# ============================================================================


def compute_source_revision(project: Project) -> str:
    """
    Compute SHA-256 source revision from canonical JSON of prompt-affecting fields.
    Delegates to project.compute_source_revision() for single source of truth.
    """
    return project.compute_source_revision()


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
    lines.extend(
        _serialize_project_header(
            project, project.provenance.source if project.provenance else None
        )
    )
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


def is_plan_stale(project: Project | None, current_draft: dict[str, Any] | None = None) -> bool:
    """Return True if plan is missing, marked stale, or current draft revision mismatches project.source_revision."""
    if not project or not getattr(project, "source_revision", None):
        return True
    if getattr(project, "is_stale", False):
        return True
    if current_draft:
        try:
            draft_rev = (
                project.compute_source_revision()
                if hasattr(project, "compute_source_revision")
                else ""
            )
            if current_draft and draft_rev:
                from .domain import compute_source_revision

                if compute_source_revision(current_draft) != project.source_revision:
                    return True
        except Exception:
            return True
    return False


def serialize_scene_video_prompt(project: Project, scene_id: int) -> str:
    """
    Serialize SCENE N block for Copy Scene Video Prompt action.

    Includes: video prompt, template exclusions, immutable negative line.
    Per Section 11.6 special copy actions.
    """
    scene = next((s for s in project.scenes if s.id == scene_id), None)
    if not scene:
        return ""

    lines = _serialize_scene(scene, scene_id)
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
        lines = []
        lines.extend(_serialize_master_image(scene))
        lines.append("")
        lines.extend(_serialize_scene(scene, 1))
    else:
        lines = _serialize_scene(scene, scene_id)

    return "\n".join(lines)


# ============================================================================
# Copy Action Results
# ============================================================================


@dataclass
class CopyActionResult:
    """Result of a copy action with metadata."""

    action: str
    scene_id: int | None
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


def redact_secrets(text: str) -> str:
    """Redact API keys, tokens, and secrets from copy/export text."""
    if not isinstance(text, str):
        return text
    redacted = re.sub(r"nvapi-[A-Za-z0-9_-]{10,}", "[REDACTED]", text)
    redacted = re.sub(
        r"Bearer\s+[A-Za-z0-9._-]+", "Bearer [REDACTED]", redacted, flags=re.IGNORECASE
    )
    return re.sub(
        r"(?:api[_-]?key|secret|token)\s*=\s*['\"][^'\"]+['\"]",
        "[REDACTED]",
        redacted,
        flags=re.IGNORECASE,
    )


def perform_copy_action(
    project: Project,
    action: str,
    scene_id: int | None = None,
    current_draft: dict[str, Any] | None = None,
) -> CopyActionResult:
    """
    Perform a specialized copy action per Section 11.6.

    Actions:
    - "master_image": Copy Master Image Prompt (first-frame prompt, exclusions, negative)
    - "scene_video": Copy Scene Video Prompt (video prompt, exclusions, negative for given scene)
    - "full_scene": Copy Full Scene (exact visible scene block)
    - "all": Copy All (full canonical plan)

    Stale Plan Block:
    - If plan is stale or draft revision mismatches, copy action is blocked.

    Args:
        project: Current project
        action: Copy action type
        scene_id: Required for scene_video and full_scene actions (1-based)
        current_draft: Optional current setup draft to check for stale plan

    Returns:
        CopyActionResult with serialized text and metadata

    Raises:
        ValueError: If plan is stale, action is unknown, or scene_id required but not provided
    """
    if is_plan_stale(project, current_draft):
        raise ValueError("Copy blocked: Plan is stale. Please rebuild plan before copying.")

    timestamp = datetime.utcnow().isoformat() + "Z"
    source_revision = project.source_revision

    if action == "master_image":
        if not project.scenes:
            raise ValueError("No scenes in project")
        scene1 = project.scenes[0]
        lines = _serialize_master_image(scene1)
        text = redact_secrets("\n".join(lines))
        return CopyActionResult(
            action="master_image",
            scene_id=1,
            text=text,
            source_revision=source_revision,
            timestamp=timestamp,
        )

    if action == "scene_video":
        if scene_id is None:
            raise ValueError("scene_id required for scene_video action")
        if scene_id < 1 or scene_id > len(project.scenes):
            raise ValueError(
                f"Invalid scene_id: {scene_id}. Project has {len(project.scenes)} scenes."
            )
        scene = project.scenes[scene_id - 1]
        lines = _serialize_scene(scene, scene_id)
        text = redact_secrets("\n".join(lines))
        return CopyActionResult(
            action="scene_video",
            scene_id=scene_id,
            text=text,
            source_revision=source_revision,
            timestamp=timestamp,
        )

    if action == "full_scene":
        if scene_id is None:
            raise ValueError("scene_id required for full_scene action")
        if scene_id < 1 or scene_id > len(project.scenes):
            raise ValueError(
                f"Invalid scene_id: {scene_id}. Project has {len(project.scenes)} scenes."
            )
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

        text = redact_secrets("\n".join(lines))
        return CopyActionResult(
            action="full_scene",
            scene_id=scene_id,
            text=text,
            source_revision=source_revision,
            timestamp=timestamp,
        )

    if action == "all":
        text = redact_secrets(serialize_full_plan(project))
        return CopyActionResult(
            action="all",
            scene_id=None,
            text=text,
            source_revision=source_revision,
            timestamp=timestamp,
        )

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
    "is_plan_stale",
    "split_prompt_negative",
    "CopyActionResult",
    "redact_secrets",
    "_canonical_json",
    "_serialize_asset_ref",
]
