from __future__ import annotations

from src.profile_types import InputMode, ScenePlan
from src.profiles.vehicle import (
    VEHICLE_ASSEMBLY_STEPS,
    VehicleCategory,
    build_scene_plans_30s,
    build_scene_plans_60s,
    make_scene_video_prompt,
    vehicle_profile,
)


def _sanitize_reserved_future_actions(actions: list[str]) -> list[str]:
    sanitized: list[str] = []
    for action in actions:
        lowered = action.lower()
        if any(
            token in lowered
            for token in (
                "final polish",
                "final reveal",
                "clean workbench",
                "hero reveal",
                "final finish",
                "fully assembled",
                "completed model",
                "reveal",
            )
        ):
            action = "later finishing stage"
        if action not in sanitized:
            sanitized.append(action)
    return sanitized


def _assert_reserved_future_continuity(scene_plans: list[ScenePlan]) -> None:
    for index, scene in enumerate(scene_plans[:-1]):
        expected_future: list[str] = []
        for future_scene in scene_plans[index + 1 :]:
            expected_future.extend(future_scene.ordered_actions)

        assert scene.reserved_future_actions == _sanitize_reserved_future_actions(expected_future)
        assert scene.forbidden_future_actions
        assert scene.forbidden_future_actions[0].startswith(
            "Do not perform this later-stage action in the current scene:"
        )
        assert scene.exact_stop_state.startswith(
            "Exact stop state after this scene's completed actions:"
        )
        assert "visibly incomplete" in scene.exact_stop_state.lower()
        assert "not-yet-used parts stay visible and untouched" in scene.exact_stop_state.lower()
        assert "edge staging tray" in scene.exact_stop_state.lower()
        assert scene.end_state
        assert scene.completion_range
        assert scene.is_final_scene is False

    final_scene = scene_plans[-1]
    assert final_scene.reserved_future_actions == []
    assert final_scene.forbidden_future_actions == []
    assert final_scene.is_final_scene is True
    assert "fully assembled" in final_scene.exact_stop_state.lower()
    assert "clean workbench" in final_scene.exact_stop_state.lower()


def test_sceneplan_backward_compatibility_defaults() -> None:
    old_payload = {
        "scene_id": 1,
        "name": "Foundation & Chassis",
        "start_state": "all parts disassembled on workbench",
        "ordered_actions": ["Engine block placed into chassis with precision"],
        "end_state": "powertrain foundation complete",
        "forbidden_changes": ["Workbench", "Lighting"],
    }

    plan = ScenePlan.from_dict(old_payload)

    assert plan.input_mode == InputMode.NONE
    assert plan.completion_range == ""
    assert plan.is_final_scene is False
    assert plan.reserved_future_actions == []
    assert plan.forbidden_future_actions == []
    assert plan.exact_stop_state == ""

    serialized = plan.to_dict()
    assert serialized["scene_id"] == 1
    assert serialized["input_mode"] == "NONE"
    assert "completion_range" in serialized
    assert "reserved_future_actions" in serialized


def test_airplane_30s_names_match_actions_ranges_and_continuity() -> None:
    scenes = build_scene_plans_30s(VehicleCategory.AIRPLANE)

    assert all(
        scene.name == f"Stage {index}: {' + '.join(scene.ordered_actions)}"
        for index, scene in enumerate(scenes, 1)
    )
    assert [scene.completion_range for scene in scenes] == ["0-30%", "30-75%", "75-100%"]
    assert scenes[0].start_state.startswith("Empty workbench")
    assert scenes[1].start_state == scenes[0].exact_stop_state
    assert scenes[2].start_state == scenes[1].exact_stop_state

    _assert_reserved_future_continuity(scenes)

    scene1 = scenes[0]
    assert "Airframe skeleton and fuselage frame assembled" in scene1.ordered_actions[0]
    assert "Engine and cockpit mount secured" in scene1.ordered_actions[1]
    assert scene1.exact_stop_state.startswith(
        "Exact stop state after this scene's completed actions:"
    )
    assert "wings" in " ".join(scene1.reserved_future_actions).lower()
    assert "landing gear" in " ".join(scene1.reserved_future_actions).lower()
    assert "propeller" in " ".join(scene1.reserved_future_actions).lower()


def test_airplane_30s_prompt_boundaries_and_final_only_rule() -> None:
    scenes = build_scene_plans_30s(VehicleCategory.AIRPLANE)

    prompt1 = make_scene_video_prompt(
        VehicleCategory.AIRPLANE,
        "P-51 Mustang",
        scenes[0].scene_id,
        scenes[0].name,
        scenes[0],
        30,
    )
    prompt2 = make_scene_video_prompt(
        VehicleCategory.AIRPLANE,
        "P-51 Mustang",
        scenes[1].scene_id,
        scenes[1].name,
        scenes[1],
        30,
    )
    prompt3 = make_scene_video_prompt(
        VehicleCategory.AIRPLANE,
        "P-51 Mustang",
        scenes[2].scene_id,
        scenes[2].name,
        scenes[2],
        30,
    )

    for prompt in (prompt1, prompt2):
        lowered = prompt.lower()
        assert "current stage range:" in lowered
        assert "start state:" in lowered
        assert "visible action sequence (" in lowered
        assert "end frame contract:" in lowered
        assert "do not invent work or begin a later stage" in lowered
        assert "must remain visibly incomplete" in lowered
        assert "fully assembled model" not in lowered
        assert "clean workbench" not in lowered
        assert "final polish" not in lowered
        assert "final reveal" not in lowered
        assert prompt.count("Negative Prompt:") == 1
        assert prompt.rstrip().endswith("blurry.")

    assert "airframe skeleton and fuselage frame assembled" in prompt1.lower()
    assert "engine and cockpit mount secured" in prompt1.lower()
    assert "wings and tail attached" not in prompt1.lower()
    assert "landing gear and control linkages installed" not in prompt1.lower()

    assert "wings and tail attached" in prompt2.lower()
    assert "landing gear and control linkages installed" in prompt2.lower()
    assert "exterior panels, canopy, and propeller fitted" not in prompt2.lower()

    final_lower = prompt3.lower()
    assert "fully assembled" in final_lower
    assert "clean workbench" in final_lower
    assert "final reveal" in final_lower
    assert "final-only permissions" in final_lower
    assert "end frame contract:" in final_lower
    assert prompt3.count("Negative Prompt:") == 1
    assert prompt3.rstrip().endswith("blurry.")


def test_six_scene_ranges_and_final_only_rules() -> None:
    scenes = build_scene_plans_60s(VehicleCategory.CAR)

    assert [scene.completion_range for scene in scenes] == [
        "0-15%",
        "15-35%",
        "35-55%",
        "55-75%",
        "75-90%",
        "90-100%",
    ]

    _assert_reserved_future_continuity(scenes)

    for scene in scenes[:-1]:
        lowered = make_scene_video_prompt(
            VehicleCategory.CAR,
            "Porsche 911",
            scene.scene_id,
            scene.name,
            scene,
            60,
        ).lower()
        assert "fully assembled model" not in lowered
        assert "clean workbench" not in lowered
        assert "final polish" not in lowered
        assert "final reveal" not in lowered
        assert "end frame contract:" in lowered
        assert "do not invent work or begin a later stage" in lowered
        assert "must remain visibly incomplete" in lowered

    final_prompt = make_scene_video_prompt(
        VehicleCategory.CAR,
        "Porsche 911",
        scenes[-1].scene_id,
        scenes[-1].name,
        scenes[-1],
        60,
    ).lower()
    assert "fully assembled" in final_prompt
    assert "clean workbench" in final_prompt
    assert "final reveal" in final_prompt
    assert "final-only permissions" in final_prompt


def test_all_categories_support_30_and_60_scene_generation() -> None:
    for category in VehicleCategory:
        scenes30 = build_scene_plans_30s(category)
        scenes60 = build_scene_plans_60s(category)

        assert len(scenes30) == 3
        assert len(scenes60) == 6
        assert scenes30[0].input_mode == InputMode.MASTER_IMAGE
        assert scenes30[1].input_mode == InputMode.PREVIOUS_FINAL_FRAME
        assert scenes60[-1].is_final_scene is True
        assert scenes30[-1].reserved_future_actions == []
        assert scenes60[-1].reserved_future_actions == []


def test_first_frame_factory_is_scene_one_only() -> None:
    scene1 = vehicle_profile.first_frame_factory(
        "airplane",
        30,
        {"vehicle_category": VehicleCategory.AIRPLANE, "model_name": "P-51 Mustang", "scene_id": 1},
    )
    scene2 = vehicle_profile.first_frame_factory(
        "airplane",
        30,
        {"vehicle_category": VehicleCategory.AIRPLANE, "model_name": "P-51 Mustang", "scene_id": 2},
    )

    assert "first_frame_prompt" in scene1
    assert scene2 == {}


def test_vehicle_assembly_steps_still_support_p_51_boundary_logic() -> None:
    airplane_steps = VEHICLE_ASSEMBLY_STEPS[VehicleCategory.AIRPLANE]

    assert airplane_steps[:3] == [
        "Airframe skeleton and fuselage frame assembled",
        "Engine and cockpit mount secured",
        "Wings and tail attached",
    ]
    assert airplane_steps[-1] == "Final polish revealing complete aircraft on clean workbench"
