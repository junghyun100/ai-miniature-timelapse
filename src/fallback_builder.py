"""
Fallback Builder Module (WP-3)

Constructs deterministic fallback scenes from local project scene plans when NVIDIA NIM
responses drop scenes, alter structure, or fail validation.

Guarantees:
- Full coverage of missing scenes (fallback scene creation).
- Strict adherence to invariant contracts:
  - Scene 1 has first_frame_prompt; Scene 2+ does NOT.
  - Identity lock in video_prompt and first_frame_prompt.
  - IMMUTABLE_NEGATIVE preserved once-last.
- Asset lineage revision computed with ancestor chain preserved.
- Provenance source correctly flagged as NIM, NIM_PARTIAL_FALLBACK, or FALLBACK.
"""

from __future__ import annotations

from typing import Any

from .domain import (
    AssetKind,
    AssetRef,
    AssetScope,
    InputMode,
    Project,
    ProvenanceSource,
    Scene,
    ScenePlan,
    StyleBible,
)
from .lineage_resolver import resolve_project_lineage
from .scene_canonicalizer import canonicalize_scene
from .serializers import IMMUTABLE_NEGATIVE


def create_fallback_scene(
    scene_id: int,
    scene_plan: ScenePlan | None,
    style_bible: StyleBible,
    profile_id: str,
    clip_duration_seconds: int = 10,
    topic: str = "",
    user_overrides: dict[str, Any] | None = None,
) -> Scene:
    """
    Constructs a single deterministic fallback scene for scene_id using local scene_plan and style_bible.
    """
    identity_lock = style_bible.identity_lock if style_bible else "Miniature timelapse style"
    scene_name = scene_plan.name if scene_plan else f"Scene {scene_id}"

    # Build video prompt from scene plan actions or default topic
    if scene_plan and scene_plan.ordered_actions:
        actions_str = ", ".join(scene_plan.ordered_actions)
        raw_video = f"{scene_name}: {scene_plan.start_state}. {actions_str}. {scene_plan.end_state}"
    else:
        raw_video = f"{scene_name} for {topic}".strip()

    # Build first frame prompt for Scene 1 only
    first_frame_prompt: str | None = None
    if scene_id == 1:
        if scene_plan and scene_plan.start_state:
            raw_ff = f"Master image showing initial workspace and setup for {topic}: {scene_plan.start_state}"
        else:
            raw_ff = f"Master image showing initial setup for {topic}"
        first_frame_prompt = raw_ff

    input_mode = InputMode.MASTER_IMAGE if scene_id == 1 else InputMode.PREVIOUS_FINAL_FRAME
    asset_scope = AssetScope.PROJECT if scene_id == 1 else AssetScope.SCENE
    logical_id = "master_image_v1" if scene_id == 1 else f"scene_{scene_id - 1}_final_frame"

    asset_ref = AssetRef(
        logical_id=logical_id,
        kind=AssetKind.IMAGE,
        scope=asset_scope,
        flow_asset_label=f"Scene {scene_id} Input Asset",
    )

    fallback_scene = Scene(
        id=scene_id,
        name=scene_name,
        input_mode=input_mode,
        asset_ref=asset_ref,
        first_frame_prompt=first_frame_prompt,
        video_prompt=raw_video,
        template_exclusions="none",
        negative_prompt=IMMUTABLE_NEGATIVE,
        clip_duration_seconds=clip_duration_seconds,
        lineage_revision="",  # Will be resolved sequentially
    )

    # Canonicalize to enforce identity lock & invariants
    return canonicalize_scene(
        fallback_scene,
        scene_id,
        identity_lock,
        scene_plan=scene_plan,
        user_overrides=user_overrides,
        profile_id=profile_id,
    )


def reconcile_scenes_with_fallback(
    nim_scene_data: list[dict[str, Any]],
    project: Project,
) -> tuple[list[Scene], list[int], ProvenanceSource]:
    """
    Reconciles NIM scene data with local project scene plans.

    Identifies missing scene IDs and creates fallback scenes for them.
    Returns:
    - List[Scene]: Fully canonicalized scenes list (1..N)
    - List[int]: Missing/fallback scene IDs
    - ProvenanceSource: NIM, NIM_PARTIAL_FALLBACK, or FALLBACK
    """
    style_bible = project.style_bible
    identity_lock = style_bible.identity_lock if style_bible else "Miniature timelapse style"
    expected_count = (
        len(project.scene_plans) if project.scene_plans else max(len(project.scenes), 1)
    )

    # Map NIM scenes by scene ID
    nim_map: dict[int, dict[str, Any]] = {}
    for s_dict in nim_scene_data:
        try:
            sid = int(s_dict.get("id", 0))
            if sid > 0:
                nim_map[sid] = s_dict
        except (ValueError, TypeError):
            continue

    resolved_scenes: list[Scene] = []
    fallback_scene_ids: list[int] = []

    for i in range(1, expected_count + 1):
        scene_plan = (
            project.scene_plans[i - 1]
            if project.scene_plans and i <= len(project.scene_plans)
            else None
        )

        if i in nim_map:
            # NIM provided data for scene i
            s_data = nim_map[i]
            video_prompt = s_data.get("video_prompt", "").strip()
            raw_additional_instruction = str(
                project.user_overrides.get("additional_instructions", "")
            ).strip()
            if raw_additional_instruction:
                video_prompt = video_prompt.replace(raw_additional_instruction, "").strip()

            # If video prompt is missing/empty, treat as fallback scene
            if not video_prompt:
                fb_scene = create_fallback_scene(
                    scene_id=i,
                    scene_plan=scene_plan,
                    style_bible=style_bible,
                    profile_id=project.profile_id,
                    clip_duration_seconds=project.clip_duration_seconds,
                    topic=project.topic,
                    user_overrides=project.user_overrides,
                )
                resolved_scenes.append(fb_scene)
                fallback_scene_ids.append(i)
            else:
                # Use NIM video prompt and canonicalize
                ff_prompt = s_data.get("first_frame_prompt") if i == 1 else None
                if ff_prompt and raw_additional_instruction:
                    ff_prompt = ff_prompt.replace(raw_additional_instruction, "").strip()
                nim_applied_overrides = {
                    key: value
                    for key, value in project.user_overrides.items()
                    if key != "additional_instructions"
                }
                name = scene_plan.name if scene_plan else f"Scene {i}"
                input_mode = InputMode.MASTER_IMAGE if i == 1 else InputMode.PREVIOUS_FINAL_FRAME

                # Existing asset_ref or construct default
                existing_scene = project.scenes[i - 1] if i <= len(project.scenes) else None
                asset_ref = (
                    existing_scene.asset_ref
                    if existing_scene
                    else AssetRef(
                        logical_id="master_image_v1" if i == 1 else f"scene_{i - 1}_final_frame",
                        kind=AssetKind.IMAGE,
                        scope=AssetScope.PROJECT if i == 1 else AssetScope.SCENE,
                    )
                )

                scene = Scene(
                    id=i,
                    name=name,
                    input_mode=input_mode,
                    asset_ref=asset_ref,
                    first_frame_prompt=ff_prompt,
                    video_prompt=video_prompt,
                    template_exclusions="none",
                    negative_prompt=IMMUTABLE_NEGATIVE,
                    clip_duration_seconds=project.clip_duration_seconds,
                    lineage_revision="",
                )

                canonical_scene = canonicalize_scene(
                    scene,
                    i,
                    identity_lock,
                    scene_plan=scene_plan,
                    user_overrides=nim_applied_overrides,
                    profile_id=project.profile_id,
                )
                resolved_scenes.append(canonical_scene)
        else:
            # Missing scene - create fallback
            fb_scene = create_fallback_scene(
                scene_id=i,
                scene_plan=scene_plan,
                style_bible=style_bible,
                profile_id=project.profile_id,
                clip_duration_seconds=project.clip_duration_seconds,
                topic=project.topic,
                user_overrides=project.user_overrides,
            )
            resolved_scenes.append(fb_scene)
            fallback_scene_ids.append(i)

    # Resolve asset lineage sequentially (incorporating ancestor hashes)
    resolved_scenes = resolve_project_lineage(resolved_scenes, project.source_revision)

    # Determine provenance source
    if not fallback_scene_ids:
        provenance_source = ProvenanceSource.NIM
    elif len(fallback_scene_ids) == expected_count:
        provenance_source = ProvenanceSource.FALLBACK
    else:
        provenance_source = ProvenanceSource.NIM_PARTIAL_FALLBACK

    return resolved_scenes, fallback_scene_ids, provenance_source
