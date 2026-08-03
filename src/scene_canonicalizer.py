"""
Scene Canonicalizer Module (WP-3)

Enforces canonical scene structures, field order, identity locks, negative prompt placement,
and Scene 1 vs Scene 2+ first-frame invariants.

Invariants:
- Scene 1 MUST have first_frame_prompt; Scenes 2+ MUST NOT (cleared if returned by NIM).
- Negative prompt MUST be strictly set to IMMUTABLE_NEGATIVE (once-last, unmutated).
- StyleBible.identity_lock MUST appear verbatim in every prompt (video_prompt & first_frame_prompt).
"""

from __future__ import annotations

from .domain import InputMode, Scene
from .profile_types import (
    STATE_PERMANENCE_RULE,
    append_scene_control_block,
    apply_master_prompt_overrides,
    state_policy_for_profile,
)
from .serializers import IMMUTABLE_NEGATIVE


def ensure_identity_lock(prompt: str, identity_lock: str) -> str:
    """
    Ensures that identity_lock appears verbatim in the prompt.
    If absent, appends identity_lock.
    """
    if not prompt or not prompt.strip():
        return identity_lock
    if identity_lock in prompt:
        return prompt.strip()

    return _append_before_negative(prompt, identity_lock)


def ensure_state_permanence(prompt: str) -> str:
    """Append the shared state permanence rule once if missing."""
    if not prompt or not prompt.strip():
        return STATE_PERMANENCE_RULE
    if STATE_PERMANENCE_RULE in prompt:
        return prompt.strip()

    return _append_before_negative(prompt, STATE_PERMANENCE_RULE)


def _append_before_negative(prompt: str, clause: str) -> str:
    """Append a required clause to the positive body, never to the negative payload."""
    marker = "Negative Prompt:"
    trimmed = prompt.strip()
    if marker not in trimmed:
        separator = " " if trimmed.endswith(".") else ". "
        return f"{trimmed}{separator}{clause}"

    body = trimmed.split(marker, 1)[0].rstrip()
    negative = trimmed.rsplit(marker, 1)[1].lstrip()
    separator = " " if body.endswith(".") else ". "
    return f"{body}{separator}{clause} {marker}{negative}"


def canonicalize_scene(
    scene: Scene,
    scene_index: int,
    identity_lock: str,
    total_scenes: int = 1,
    scene_plan: object | None = None,
    user_overrides: dict | None = None,
    profile_id: str = "",
) -> Scene:
    """
    Canonicalizes a Scene instance:
    1. Enforces Scene 1 first-frame prompt presence, Scene 2+ first-frame prompt removal.
    2. Enforces InputMode (MASTER_IMAGE for Scene 1, PREVIOUS_FINAL_FRAME for Scene 2+).
    3. Enforces identity_lock presence in prompts.
    4. Enforces IMMUTABLE_NEGATIVE on negative_prompt (no mutation).
    """
    # 1. Scene 1 vs Scene 2+ first frame invariant
    if scene_index == 1:
        scene.input_mode = InputMode.MASTER_IMAGE
        if not scene.first_frame_prompt:
            # Fallback text if first_frame_prompt missing for Scene 1
            scene.first_frame_prompt = f"Master image setup for scene 1, {identity_lock}"
        else:
            scene.first_frame_prompt = ensure_identity_lock(scene.first_frame_prompt, identity_lock)
        scene.first_frame_prompt = apply_master_prompt_overrides(
            scene.first_frame_prompt, user_overrides
        )
    else:
        # Failure Rule: Scene 2+ first frame MUST NOT be regenerated or kept
        scene.input_mode = InputMode.PREVIOUS_FINAL_FRAME
        scene.first_frame_prompt = None

    # 2. Identity Lock in Video Prompt
    scene.video_prompt = ensure_state_permanence(
        ensure_identity_lock(scene.video_prompt, identity_lock)
    )
    if scene_plan is not None:
        scene.video_prompt = append_scene_control_block(
            scene.video_prompt,
            scene_plan,
            user_overrides,
            state_policy_for_profile(profile_id),
        )

    # 3. Negative Once-Last (Immutable Negative)
    # Failure Rule: negative line must not be mutated or altered
    scene.negative_prompt = IMMUTABLE_NEGATIVE

    # 4. Ensure ID is 1-indexed matching scene_index
    scene.id = scene_index

    return scene
