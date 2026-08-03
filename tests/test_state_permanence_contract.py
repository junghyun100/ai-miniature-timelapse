from __future__ import annotations

from src.domain import AssetKind, AssetRef, AssetScope, InputMode, Scene
from src.profile_types import (
    ScenePlan,
    append_scene_control_block,
    apply_master_prompt_overrides,
)
from src.profiles.architecture import make_first_frame_prompt as architecture_first_frame_prompt
from src.profiles.architecture import make_scene_video_prompt as architecture_video_prompt
from src.profiles.cooking import make_scene_video_prompt as cooking_video_prompt
from src.profiles.home_decor import make_scene_video_prompt as home_decor_video_prompt
from src.profiles.product import make_scene_video_prompt as product_video_prompt
from src.profiles.vehicle import VehicleCategory
from src.profiles.vehicle import make_scene_video_prompt as vehicle_video_prompt
from src.scene_canonicalizer import canonicalize_scene
from src.serializers import IMMUTABLE_NEGATIVE


def _dummy_scene(scene_id: int, video_prompt: str, first_frame_prompt: str | None = None) -> Scene:
    return Scene(
        id=scene_id,
        name=f"Scene {scene_id}",
        input_mode=InputMode.MASTER_IMAGE if scene_id == 1 else InputMode.PREVIOUS_FINAL_FRAME,
        asset_ref=AssetRef(
            logical_id=f"scene_{scene_id:02d}",
            kind=AssetKind.IMAGE,
            scope=AssetScope.SCENE,
        ),
        first_frame_prompt=first_frame_prompt,
        video_prompt=video_prompt,
        template_exclusions="",
        negative_prompt=IMMUTABLE_NEGATIVE,
        clip_duration_seconds=10,
        lineage_revision="sha256:" + "0" * 64,
    )


def test_architecture_scene_one_starts_from_bare_ground():
    prompt = architecture_first_frame_prompt("hanok")

    lowered = prompt.lower()
    assert "bare sand or soil" in lowered
    assert "no foundation" in lowered
    assert "no later-stage elements" in lowered


def test_architecture_video_prompt_carries_state_permanence():
    prompt = architecture_video_prompt(2, "hanok", 30)

    lowered = prompt.lower()
    assert "current stage range: 35-75%" in lowered
    assert "end frame contract" in lowered
    assert "keep every already-built structural element" in lowered


def test_vehicle_video_prompt_carries_state_permanence():
    prompt = vehicle_video_prompt(
        VehicleCategory.CAR, "Porsche 911", 1, "Foundation & Chassis", total_duration=30
    )

    lowered = prompt.lower()
    assert "keep every already-installed" in lowered
    assert "must remain visibly incomplete" in lowered


def test_product_video_prompt_carries_state_permanence():
    prompt = product_video_prompt(1, "watch", 30)

    lowered = prompt.lower()
    assert "keep every already-installed component" in lowered
    assert "installed parts remain visible and fixed" in lowered


def test_cooking_and_home_decor_prompts_carry_state_permanence():
    cooking_prompt = cooking_video_prompt(2, "kimchi_jjigae")
    home_prompt = home_decor_video_prompt(
        "Hanji bottle lantern",
        "버린 병에 한지를 붙이면 등불이 돼요",
        ["hanji paper", "discarded glass bottle", "silk thread"],
        "Korean lotus bottle lantern",
    )

    assert "keep every already-installed" in cooking_prompt.lower()
    assert "prepared ingredients and cookware remain visible and fixed" in cooking_prompt.lower()
    assert "keep every already-installed" in home_prompt.lower()


def test_canonicalizer_restores_state_permanence():
    scene = _dummy_scene(1, "Build the foundation.")
    canonical = canonicalize_scene(scene, 1, "Identity lock for hanok")

    assert "identity lock for hanok" in canonical.video_prompt.lower()
    assert "keep every already-installed" in canonical.video_prompt.lower()


def test_shared_control_block_preserves_terminal_negative_once_and_applies_overrides():
    plan = ScenePlan(
        scene_id=1,
        name="Foundation",
        start_state="Bare ground with no structure installed",
        ordered_actions=["mark footprint", "level ground", "place foundation"],
        end_state="Foundation complete",
        forbidden_changes=[],
        reserved_future_actions=["raise walls", "install roof"],
        exact_stop_state="Foundation complete, walls not started",
    )
    prompt = append_scene_control_block(
        "Build the foundation. Negative Prompt: old. Negative Prompt: final.",
        plan,
        {"scale": "subject occupies 70% of frame"},
    )

    assert prompt.count("Negative Prompt:") == 1
    assert prompt.rstrip().endswith("Negative Prompt:final.")
    assert prompt.startswith("INPUT FRAME LOCK:")
    assert "immutable visual ground truth" in prompt
    assert "visible action sequence (3 physically observable actions)" in prompt.lower()
    assert "edge staging tray" in prompt
    assert "USER OVERRIDE LOCK (HIGH PRIORITY)" in prompt
    assert "required scale and composition: subject occupies 70% of frame" in prompt
    assert prompt.index("USER OVERRIDE LOCK") < prompt.index("START STATE")
    assert "TEMPORAL DELTA LOCK" in prompt
    assert "Never morph, redesign, replace, remove, rescale" in prompt
    assert prompt.index("END FRAME CONTRACT") < prompt.index("PROMPT BODY:")
    assert (
        append_scene_control_block(
            prompt,
            plan,
            {"scale": "subject occupies 70% of frame"},
        )
        == prompt
    )


def test_master_prompt_establishes_scale_before_the_visual_body():
    prompt = apply_master_prompt_overrides(
        "Macro image body. Negative Prompt: fixed.",
        {"scale": "subject occupies approximately 82% of the frame"},
    )

    assert prompt.startswith("MASTER COMPOSITION CONTRACT:")
    assert prompt.index("subject occupies approximately 82%") < prompt.index("MASTER PROMPT BODY:")
    assert "immutable scale reference for every later scene" in prompt
    assert prompt.count("Negative Prompt:") == 1
    assert prompt.rstrip().endswith("Negative Prompt:fixed.")
    assert (
        apply_master_prompt_overrides(
            prompt, {"scale": "subject occupies approximately 82% of the frame"}
        )
        == prompt
    )


def test_final_scene_allows_reveal_only_after_work_and_cleanup():
    plan = ScenePlan(
        scene_id=3,
        name="Final reveal",
        start_state="Nearly complete subject",
        ordered_actions=["finish details", "clean workspace", "reveal"],
        end_state="Clean completed subject",
        forbidden_changes=[],
        exact_stop_state="Clean completed subject in hero frame",
        is_final_scene=True,
    )

    prompt = append_scene_control_block("Finish and reveal.", plan)

    assert "During all listed work and cleanup, never rescale, reframe" in prompt
    assert "Only after every listed action and cleanup is complete" in prompt
    assert "explicitly listed final reveal change framing" in prompt


def test_canonicalizer_keeps_identity_and_state_rules_before_negative_prompt():
    scene = _dummy_scene(
        1,
        "Build in order. Negative Prompt: fixed.",
        "Unstarted master image. Negative Prompt: fixed.",
    )
    plan = ScenePlan(
        scene_id=1,
        name="Foundation",
        start_state="Bare ground",
        ordered_actions=["mark", "level", "place"],
        end_state="Foundation complete",
        forbidden_changes=[],
        exact_stop_state="Foundation complete and nothing more",
    )

    canonical = canonicalize_scene(
        scene,
        1,
        "LOCKED SUBJECT IDENTITY",
        scene_plan=plan,
        user_overrides={"scale": "subject occupies 82% of frame"},
        profile_id="architecture.korean",
    )

    video_body, video_negative = canonical.video_prompt.split("Negative Prompt:", 1)
    master_body, master_negative = canonical.first_frame_prompt.split("Negative Prompt:", 1)
    assert "LOCKED SUBJECT IDENTITY" in video_body
    assert "TEMPORAL DELTA LOCK" in video_body
    assert "LOCKED SUBJECT IDENTITY" not in video_negative
    assert "LOCKED SUBJECT IDENTITY" in master_body
    assert "subject occupies 82% of frame" in master_body
    assert "LOCKED SUBJECT IDENTITY" not in master_negative


def test_every_profile_uses_shared_scene_control_contract():
    prompts = [
        architecture_video_prompt(1, "hanok", 30),
        vehicle_video_prompt(
            VehicleCategory.CAR, "Porsche 911", 1, "Foundation & Chassis", total_duration=30
        ),
        product_video_prompt(1, "watch", 30),
        cooking_video_prompt(1, "kimchi_jjigae"),
        home_decor_video_prompt(
            "Hanji bottle lantern",
            "버린 병에 한지를 붙이면 등불이 돼요",
            ["hanji paper", "discarded glass bottle", "silk thread"],
            "Korean lotus bottle lantern",
        ),
    ]

    for prompt in prompts:
        lowered = prompt.lower()
        assert prompt.startswith("INPUT FRAME LOCK:")
        assert "immutable visual ground truth" in lowered
        assert "current stage range:" in lowered
        assert "state rule:" in lowered
        assert "visible action sequence (" in lowered
        assert "temporal delta lock:" in lowered
        assert "never morph, redesign, replace, remove" in lowered
        assert (
            "never morph, redesign, replace, remove, rescale" in lowered
            or "only after every listed action and cleanup is complete" in lowered
        )
        assert "end frame contract:" in lowered
        assert prompt.index("END FRAME CONTRACT:") < prompt.index("PROMPT BODY:")
        assert prompt.count("Negative Prompt:") == 1
