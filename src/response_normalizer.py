"""
Response Normalizer Module (WP-3)

Parses, normalizes, and validates NVIDIA NIM responses, handling header deletions,
negative prompt alterations, and missing scenes via fallback builder, scene canonicalizer,
and lineage resolver.

Guarantees:
- Safe response parsing (handles raw JSON string, code block wrappers, missing headers).
- Field order normalization (header -> master image -> canonical scene order).
- Enforces invariant contracts:
  - Scene 1 first-frame prompt presence, Scene 2+ first-frame prompt removal.
  - Identity lock in video_prompt and first_frame_prompt.
  - IMMUTABLE_NEGATIVE re-inserted once-last per scene/master image block.
- Lineage hash recomputation with ancestor chain preserved.
- Full provenance tracking with fallback scene coverage.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from .domain import Project, Provenance
from .fallback_builder import reconcile_scenes_with_fallback
from .serializers import serialize_full_plan


def parse_raw_nim_response(
    raw_response: str | dict[str, Any],
    expected_request_id: str | None = None,
    expected_source_revision: str | None = None,
) -> dict[str, Any]:
    """
    Parses a raw NIM response (string or dict), stripping markdown fences if present.
    Restores missing header fields if stripped by NIM.
    """
    if isinstance(raw_response, dict):
        data = dict(raw_response)
    elif isinstance(raw_response, str):
        cleaned = raw_response.strip()
        # Remove ```json ... ``` markdown block wrappers
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as err:
            raise ValueError(f"Failed to parse NIM JSON response: {err}")
    else:
        raise TypeError(f"Unsupported response type: {type(raw_response)}")

    # Header Restoration & Staleness Check
    if expected_request_id:
        req_id = data.get("request_id")
        if not req_id:
            data["request_id"] = expected_request_id
        elif str(req_id) != str(expected_request_id):
            raise ValueError(
                f"Stale NIM response: request_id mismatch (got {req_id}, expected {expected_request_id})"
            )

    if expected_source_revision:
        src_rev = data.get("source_revision")
        if not src_rev:
            data["source_revision"] = expected_source_revision
        elif src_rev != expected_source_revision:
            raise ValueError(
                f"Stale NIM response: source_revision mismatch (got {src_rev}, expected {expected_source_revision})"
            )

    if "schema_version" not in data:
        data["schema_version"] = "2.0"

    return data


def normalize_nim_response(
    raw_response: str | dict[str, Any],
    project: Project,
    model_id: str = "nvidia/nemotron-3-ultra-550b-a55b",
    expected_request_id: str | None = None,
) -> tuple[Project, Provenance]:
    """
    Complete post-normalization pipeline for NIM responses:
    1. Response parse & header restoration
    2. Missing scene detection & fallback scene creation
    3. Scene canonicalization (Scene 1 first-frame, Scene 2+ no first-frame, identity lock, negative once-last)
    4. Lineage hash recomputation with ancestor chain preserved
    5. Field order normalization & Provenance creation

    Returns (updated_project, provenance)
    """
    source_revision = project.source_revision or project.compute_source_revision()
    req_id = expected_request_id or (
        project.provenance.request_id if project.provenance else "req_local"
    )

    validation_warnings: list[str] = []

    # 1. Response Parse
    try:
        data = parse_raw_nim_response(
            raw_response=raw_response,
            expected_request_id=req_id,
            expected_source_revision=source_revision,
        )
        nim_scenes = data.get("scenes", [])
        if not isinstance(nim_scenes, list):
            nim_scenes = []
            validation_warnings.append("NIM response scenes field was not a list; using fallbacks")
    except Exception as err:
        nim_scenes = []
        validation_warnings.append(
            f"Failed to parse NIM response payload ({err}); falling back to local plans"
        )

    # 2 & 3 & 4. Scene Fallback, Canonicalization, and Lineage Resolution
    canonical_scenes, fallback_scene_ids, prov_source = reconcile_scenes_with_fallback(
        nim_scene_data=nim_scenes,
        project=project,
    )

    if fallback_scene_ids:
        validation_warnings.append(f"Used fallback scenes for scene IDs: {fallback_scene_ids}")

    # Update project scenes
    project.scenes = canonical_scenes
    project.scene_count = len(canonical_scenes)

    # 5. Provenance Creation
    provenance = Provenance(
        source=prov_source,
        provider="nvidia_nim",
        model_id=model_id,
        base_url_label="NVIDIA Integrate API",
        generated_at=datetime.now(UTC),
        request_id=req_id,
        source_revision=source_revision,
        fallback_scene_ids=fallback_scene_ids,
        validation_warnings=validation_warnings,
    )

    project.provenance = provenance
    return project, provenance


def normalize_field_order(project: Project) -> str:
    """
    Generates canonical serialized plan with strict field order:
    1. Project Header
    2. MASTER IMAGE (Scene 1 only)
    3. SCENE 1..N blocks (with IMMUTABLE_NEGATIVE once-last)
    """
    return serialize_full_plan(project)
