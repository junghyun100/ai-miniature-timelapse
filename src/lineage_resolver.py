"""
Lineage Resolver Module (WP-3)

Computes and resolves asset lineage hashes and lineage revisions for scenes,
preserving ancestor lineage continuity across fallbacks and canonicalization.

Invariants:
- Asset lineage hash/revision MUST incorporate ancestor lineage (parent scene's lineage revision).
- Must never drop or lose ancestor history ("lineage hash ancestor 누락" failure rule).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .domain import AssetRef, Scene


def compute_scene_lineage_revision(
    scene_id: int,
    source_revision: str,
    video_prompt: str,
    first_frame_prompt: str | None,
    asset_ref: AssetRef,
    parent_lineage_revision: str | None = None,
) -> str:
    """
    Computes a deterministic SHA-256 lineage revision for a scene.

    The computation explicitly includes:
    - scene_id
    - source_revision (project-level revision)
    - parent_lineage_revision (ancestor lineage chain - MUST NOT BE DROPPED for Scene 2+)
    - asset_ref logical_id and content_hash
    - prompts (video_prompt and first_frame_prompt)
    """
    payload: dict[str, Any] = {
        "scene_id": scene_id,
        "source_revision": source_revision,
        "parent_lineage_revision": parent_lineage_revision
        or ("root" if scene_id == 1 else "ancestor_missing"),
        "asset_logical_id": asset_ref.logical_id if asset_ref else "",
        "asset_content_hash": asset_ref.content_hash if asset_ref else None,
        "video_prompt": video_prompt or "",
        "first_frame_prompt": first_frame_prompt or "",
    }

    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def resolve_project_lineage(scenes: list[Scene], source_revision: str) -> list[Scene]:
    """
    Resolves and updates lineage_revision for all scenes in sequence,
    ensuring each scene's lineage revision incorporates its ancestor's lineage revision.

    Returns the updated scenes list with lineage_revision set on both Scene and AssetRef.
    """
    parent_lineage: str | None = None

    for idx, scene in enumerate(scenes):
        scene_id = scene.id or (idx + 1)

        # For Scene 2+, ensure parent_lineage is present from previous scene
        if idx > 0 and parent_lineage is None:
            # Fallback ancestor marker if previous scene had no lineage_revision
            parent_lineage = scenes[idx - 1].lineage_revision or "ancestor_root"

        lineage_rev = compute_scene_lineage_revision(
            scene_id=scene_id,
            source_revision=source_revision,
            video_prompt=scene.video_prompt,
            first_frame_prompt=scene.first_frame_prompt,
            asset_ref=scene.asset_ref,
            parent_lineage_revision=parent_lineage,
        )

        scene.lineage_revision = lineage_rev
        if scene.asset_ref:
            scene.asset_ref.lineage_revision = lineage_rev

        # Current scene's lineage becomes the ancestor for the next scene
        parent_lineage = lineage_rev

    return scenes
