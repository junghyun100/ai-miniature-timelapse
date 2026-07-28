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
from .profile_types import STATE_PERMANENCE_RULE
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

    # Append identity lock cleanly
    trimmed = prompt.strip()
    if trimmed.endswith("."):
        return f"{trimmed} {identity_lock}"
    return f"{trimmed}, {identity_lock}"


def ensure_state_permanence(prompt: str) -> str:
    """Append the shared state permanence rule once if missing."""
    if not prompt or not prompt.strip():
        return STATE_PERMANENCE_RULE
    if STATE_PERMANENCE_RULE in prompt:
        return prompt.strip()

    trimmed = prompt.strip()
    if trimmed.endswith("."):
        return f"{trimmed} {STATE_PERMANENCE_RULE}"
    return f"{trimmed}. {STATE_PERMANENCE_RULE}"


def canonicalize_scene(
    scene: Scene,
    scene_index: int,
    identity_lock: str,
    total_scenes: int = 1,
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
    else:
        # Failure Rule: Scene 2+ first frame MUST NOT be regenerated or kept
        scene.input_mode = InputMode.PREVIOUS_FINAL_FRAME
        scene.first_frame_prompt = None

    # 2. Identity Lock in Video Prompt
    scene.video_prompt = ensure_state_permanence(
        ensure_identity_lock(scene.video_prompt, identity_lock)
    )

    # 3. Negative Once-Last (Immutable Negative)
    # Failure Rule: negative line must not be mutated or altered
    scene.negative_prompt = IMMUTABLE_NEGATIVE

    # 4. Ensure ID is 1-indexed matching scene_index
    scene.id = scene_index

    return scene
