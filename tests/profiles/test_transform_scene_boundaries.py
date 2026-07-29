from __future__ import annotations

import pytest

from src.profile_types import PROFILE_REGISTRY
from src.profiles.cooking import (
    SCENE_PLANS_30S as COOKING_SCENE_PLANS,
)
from src.profiles.cooking import (
    cooking_profile,
)
from src.profiles.cooking import (
    make_first_frame_prompt as cooking_make_first_frame_prompt,
)
from src.profiles.cooking import (
    make_scene_video_prompt as cooking_make_scene_video_prompt,
)
from src.profiles.home_decor import (
    home_decor_profile,
)
from src.profiles.home_decor import (
    make_scene_video_prompt as home_decor_make_scene_video_prompt,
)


def _assert_negative_prompt_once_and_last(prompt: str, expected_suffix: str) -> None:
    assert prompt.count("Negative Prompt:") == 1
    assert prompt.rstrip().endswith(expected_suffix)


def test_cooking_scene_boundaries_and_final_only_contract() -> None:
    profile = PROFILE_REGISTRY["cooking.miniature"]
    assert profile is cooking_profile
    assert profile.allowed_total_durations == [30]
    assert len(profile.scene_plans) == 3

    scene1, scene2, scene3 = profile.scene_plans
    assert [scene.completion_range for scene in profile.scene_plans] == ["0-35%", "35-80%", "80-100%"]
    assert scene1.start_state.startswith("Raw ingredients only")
    assert scene1.exact_stop_state == scene2.start_state
    assert scene2.exact_stop_state == scene3.start_state
    assert scene1.is_final_scene is False
    assert scene2.is_final_scene is False
    assert scene3.is_final_scene is True
    assert scene1.reserved_future_actions == [
        *COOKING_SCENE_PLANS[1].ordered_actions,
        *COOKING_SCENE_PLANS[2].ordered_actions,
    ]
    assert scene2.reserved_future_actions == COOKING_SCENE_PLANS[2].ordered_actions
    assert scene3.reserved_future_actions == []
    assert scene1.forbidden_future_actions
    assert scene2.forbidden_future_actions
    assert scene3.forbidden_future_actions == []

    first_frame = cooking_make_first_frame_prompt("kimchi_jjigae")
    assert "raw ingredients for Kimchi Jjigae" in first_frame
    assert "No cutting or heat yet" in first_frame
    _assert_negative_prompt_once_and_last(first_frame, "talking.")

    prompt1 = cooking_make_scene_video_prompt(1, "kimchi_jjigae")
    prompt2 = cooking_make_scene_video_prompt(2, "kimchi_jjigae")
    prompt3 = cooking_make_scene_video_prompt(3, "kimchi_jjigae")

    for prompt in (prompt1, prompt2):
        lowered = prompt.lower()
        for forbidden_token in ("finished dish", "reveal", "hero", "plating", "plated"):
            assert forbidden_token not in lowered
        assert "reserved next-stage actions" not in lowered
        assert "exact input/start state" in lowered
        assert "exact stop state" in lowered
        _assert_negative_prompt_once_and_last(prompt, "talking.")

    final_lower = prompt3.lower()
    assert "garnish" in final_lower
    assert "plated" in final_lower
    assert "hero reveal" in final_lower
    assert "finished plated dish" in final_lower
    _assert_negative_prompt_once_and_last(prompt3, "talking.")


def test_home_decor_single_clip_final_contract() -> None:
    profile = PROFILE_REGISTRY["home_decor.diy"]
    assert profile is home_decor_profile
    assert profile.allowed_total_durations == [10]
    assert len(profile.scene_plans) == 1

    scene = profile.scene_plans[0]
    assert scene.completion_range == "0-100%"
    assert scene.is_final_scene is True
    assert scene.reserved_future_actions == []
    assert scene.forbidden_future_actions == []
    assert scene.start_state.startswith("Raw craft materials")
    assert "Final object reveal" in scene.exact_stop_state

    first_frame = profile.first_frame_factory(
        "home_decor.diy",
        10,
        {
            "idea_name": "Traditional Lotus Mood Lamp",
            "materials": ["hanji", "plastic spoon", "wire", "glue"],
            "final_object": "Traditional Lotus Mood Lamp",
            "scene_id": 1,
        },
    )["first_frame_prompt"]
    assert "raw craft materials" in first_frame.lower()
    assert "no completed craft visible" in first_frame.lower()

    prompt = home_decor_make_scene_video_prompt(
        craft_name="Traditional Lotus Mood Lamp",
        korean_narration="버려진 숟가락이 연꽃이 되다니 손으로 접으니 피어나네요",
        materials=["hanji", "plastic spoon", "wire", "glue"],
        final_object="Traditional Lotus Mood Lamp",
    )

    assert "Single 10-second continuous clip" in prompt
    assert "Opening Hook" in prompt
    assert "Introducing Materials" in prompt
    assert "Building Begins" in prompt
    assert "Mid-Build Sequence" in prompt
    assert "Detail Showcase" in prompt
    assert "Final Reveal" in prompt
    assert "Korean female voiceover narrates continuously" in prompt
    assert "No background music." in prompt
    _assert_negative_prompt_once_and_last(prompt, "blurry.")


@pytest.mark.parametrize(
    "invalid_narration",
    [
        "",
        " \n\t ",
        "가" * 61,
    ],
)
def test_home_decor_rejects_invalid_non_whitespace_narration_length(
    invalid_narration: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="1 to 60 non-whitespace characters",
    ):
        home_decor_make_scene_video_prompt(
            craft_name="Traditional Lotus Mood Lamp",
            korean_narration=invalid_narration,
            materials=["hanji", "wire"],
            final_object="Traditional Lotus Mood Lamp",
        )


def test_home_decor_accepts_exactly_sixty_non_whitespace_characters() -> None:
    prompt = home_decor_make_scene_video_prompt(
        craft_name="Traditional Lotus Mood Lamp",
        korean_narration="가 " * 60,
        materials=["hanji", "wire"],
        final_object="Traditional Lotus Mood Lamp",
    )

    assert '"가 ' in prompt
    _assert_negative_prompt_once_and_last(prompt, "blurry.")


def test_scene_prompt_signatures_remain_backward_compatible() -> None:
    cooking_prompt = cooking_make_scene_video_prompt(2, "bibimbap")
    home_decor_prompt = home_decor_make_scene_video_prompt(
        craft_name="Paper Flower Ornament",
        korean_narration="종이꽃이 피어나요",
        materials=["hanji", "wire"],
        final_object="Paper Flower Ornament",
    )

    assert "paper flower ornament" in home_decor_prompt.lower()
    _assert_negative_prompt_once_and_last(cooking_prompt, "talking.")
    _assert_negative_prompt_once_and_last(home_decor_prompt, "blurry.")
