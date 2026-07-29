from __future__ import annotations

import importlib

from src.profile_types import InputMode
from src.profiles.product import (
    PRODUCT_SUBTYPE_STAGES,
    PRODUCT_SUBTYPES,
    SCENE_PLAN_10S,
    SCENE_PLANS_30S,
    SCENE_PLANS_60S,
    _build_scene_plans,
    make_scene_video_prompt,
    product_profile,
)

EXPECTED_RANGES = {
    10: ["0-100%"],
    30: ["0-30%", "30-75%", "75-100%"],
    60: ["0-15%", "15-35%", "35-55%", "55-75%", "75-90%", "90-100%"],
}


def _positive_prompt(prompt: str) -> str:
    return prompt.split("Negative Prompt:", maxsplit=1)[0].lower()


def _assert_scene_contract(subtype: str, duration: int) -> None:
    scenes = _build_scene_plans(subtype, duration)

    assert [scene.completion_range for scene in scenes] == EXPECTED_RANGES[duration]
    assert scenes[0].input_mode == InputMode.MASTER_IMAGE
    assert scenes[0].start_state == "All parts disassembled on workbench"

    for index, scene in enumerate(scenes):
        prompt = make_scene_video_prompt(
            scene.scene_id,
            subtype,
            duration,
            scene,
        )
        positive = _positive_prompt(prompt)

        assert prompt.count("Negative Prompt:") == 1
        assert prompt.rstrip().endswith(
            "floating parts, teleporting parts, completed model at start, messy final workbench."
        )
        assert "giant human hands only" in positive
        assert "no floating or teleporting parts" in positive
        assert "camera angle, scale, workbench position, and lighting physically fixed" in positive

        if index:
            assert scene.input_mode == InputMode.PREVIOUS_FINAL_FRAME
            assert scene.start_state == scenes[index - 1].exact_stop_state

        if scene.is_final_scene:
            assert scene.reserved_future_actions == []
            assert scene.forbidden_future_actions == []
            assert "fully assembled" in positive
            assert "clean workbench" in positive
            assert "final brush sweep" in positive
        else:
            expected_future = [
                action
                for future_scene in scenes[index + 1 :]
                for action in future_scene.ordered_actions
            ]
            assert scene.reserved_future_actions
            assert scene.forbidden_future_actions == scene.reserved_future_actions
            assert all(action in scene.reserved_future_actions for action in expected_future[:-1])
            assert "completion range:" in positive
            assert "ordered current actions:" in positive
            assert "exact stop state:" in positive
            assert "prohibited future work:" in positive
            assert "leave all future parts separate, visible, and untouched" in positive
            assert "fully assembled" not in positive
            assert "clean workbench" not in positive
            assert "final brush" not in positive


def test_product_module_imports_and_default_scene_plans_are_valid() -> None:
    module = importlib.import_module("src.profiles.product")

    assert module.product_profile is product_profile
    assert _build_scene_plans("watch", 10) == SCENE_PLAN_10S
    assert _build_scene_plans("watch", 30) == SCENE_PLANS_30S
    assert _build_scene_plans("watch", 60) == SCENE_PLANS_60S
    assert product_profile.scene_plans == SCENE_PLAN_10S


def test_product_10_30_60_scene_boundary_contracts() -> None:
    for duration in (10, 30, 60):
        _assert_scene_contract("watch", duration)


def test_product_subtype_stages_drive_generated_scene_actions() -> None:
    for subtype in PRODUCT_SUBTYPES:
        scenes = _build_scene_plans(subtype, 60)

        assert len(scenes) == 6
        assert [scene.ordered_actions[0] for scene in scenes] == PRODUCT_SUBTYPE_STAGES[subtype]
        _assert_scene_contract(subtype, 30)
        _assert_scene_contract(subtype, 60)
