from __future__ import annotations

from src.profiles.architecture import (
    ARCH_NEGATIVE_BASE,
    ARCHITECTURE_INITIAL_STATE,
    ARCHITECTURE_SUBTYPES,
    get_scene_plans,
    make_first_frame_prompt,
    make_scene_video_prompt,
)

EXPECTED_30S_RANGES = ["0-35%", "35-75%", "75-100%"]
EXPECTED_60S_RANGES = ["0-15%", "15-35%", "35-55%", "55-75%", "75-90%", "90-100%"]
EXPECTED_30S_NAMES = [
    "Foundation & Walls",
    "Roofing & Exterior",
    "Painting & Landscaping Reveal",
]
EXPECTED_60S_NAMES = [
    "Foundation",
    "Wall & Windows",
    "Roofing",
    "Exterior",
    "Painting",
    "Landscaping & Reveal",
]
NON_FINAL_FORBIDDEN_PHRASES = [
    "final reveal",
    "normal cinematic speed",
    "completed building",
    "landscaping reveal",
    "tools removed",
]
REQUIRED_BOUNDARY_PHRASES = [
    "CURRENT STAGE RANGE:",
    "stop immediately at the end-frame contract",
    "do not proceed beyond it",
]
REQUIRED_GLOBAL_PHRASES = [
    "ultra fast timelapse speed",
    "human hands continuously constructing and moving rapidly",
    "rapid procedural timelapse in one uninterrupted locked camera composition",
    "no editorial cuts or alternate shots",
    "cinematic macro photography",
]

EXPECTED_SUBTYPES = {
    "hanok",
    "palace",
    "temple",
    "seowon",
    "modern_hanok",
    "dolmen",
    "villa",
    "store",
    "school",
    "hotel",
    "apartment",
    "factory",
    "barn",
}


def _assert_chain(scene_plans) -> None:
    assert scene_plans[0].start_state.startswith("Completely unstarted site")
    for previous, current in zip(scene_plans, scene_plans[1:], strict=False):
        assert current.start_state == previous.exact_stop_state


def _assert_non_final_prompt(prompt: str, exact_stop_state: str) -> None:
    lowered = prompt.lower()
    for phrase in REQUIRED_BOUNDARY_PHRASES + REQUIRED_GLOBAL_PHRASES:
        assert phrase.lower() in lowered
    assert exact_stop_state.lower() in lowered
    assert "edge staging tray" in lowered
    assert "start no new work" in lowered
    for phrase in NON_FINAL_FORBIDDEN_PHRASES:
        assert phrase not in lowered
    assert prompt.count("Negative Prompt:") == 1
    assert prompt.rstrip().endswith(ARCH_NEGATIVE_BASE)


def _assert_final_prompt(prompt: str) -> None:
    lowered = prompt.lower()
    for phrase in REQUIRED_GLOBAL_PHRASES:
        assert phrase in lowered
    assert "final-only work may include landscaping" in lowered
    assert "hands removed from frame" in lowered
    assert "normal cinematic speed" in lowered
    assert "cinematic zoom-out reveal" in lowered
    assert prompt.count("Negative Prompt:") == 1
    assert prompt.rstrip().endswith(ARCH_NEGATIVE_BASE)


def test_30s_and_60s_scene_ranges_chain_and_reserved_actions() -> None:
    plans_30 = get_scene_plans(30)
    plans_60 = get_scene_plans(60)

    assert [scene.completion_range for scene in plans_30] == EXPECTED_30S_RANGES
    assert [scene.completion_range for scene in plans_60] == EXPECTED_60S_RANGES
    assert [scene.name for scene in plans_30] == EXPECTED_30S_NAMES
    assert [scene.name for scene in plans_60] == EXPECTED_60S_NAMES

    _assert_chain(plans_30)
    _assert_chain(plans_60)

    assert all(scene.reserved_future_actions for scene in plans_30[:-1])
    assert plans_30[-1].reserved_future_actions == []
    assert all(scene.reserved_future_actions for scene in plans_60[:-1])
    assert plans_60[-1].reserved_future_actions == []


def test_python_registry_matches_ui_13_subtype_parity() -> None:
    assert set(ARCHITECTURE_SUBTYPES) == EXPECTED_SUBTYPES

    for _subtype, data in ARCHITECTURE_SUBTYPES.items():
        assert data["label"]
        assert data["materials"]
        assert data["key_features"]
        assert data["color_palette"]["primary"]
        assert data["color_palette"]["accent"]
        assert data["color_palette"]["tone"]


def test_master_image_and_scene_one_share_completely_unstarted_state() -> None:
    first_frame = make_first_frame_prompt("hanok")

    assert ARCHITECTURE_INITIAL_STATE in first_frame
    assert get_scene_plans(30)[0].start_state == ARCHITECTURE_INITIAL_STATE
    assert get_scene_plans(60)[0].start_state == ARCHITECTURE_INITIAL_STATE
    assert "partially prepared" not in first_frame.lower()
    assert "nothing has been built yet" in first_frame.lower()


def test_non_final_prompts_respect_scene_boundaries() -> None:
    plans = get_scene_plans(60)
    subtype = "hanok"

    for scene in plans[:-1]:
        prompt = make_scene_video_prompt(
            scene.scene_id,
            subtype,
            duration_seconds=60,
            scene_plan=scene,
        )
        _assert_non_final_prompt(prompt, scene.exact_stop_state)


def test_final_prompt_contains_final_only_terms() -> None:
    final_scene = get_scene_plans(60)[-1]
    prompt = make_scene_video_prompt(
        final_scene.scene_id,
        "palace",
        duration_seconds=60,
        scene_plan=final_scene,
    )
    _assert_final_prompt(prompt)


def test_subtype_specific_prompts_cover_multiple_korean_architectures() -> None:
    samples = [
        ("hanok", get_scene_plans(30)[0]),
        ("temple", get_scene_plans(30)[1]),
        ("palace", get_scene_plans(60)[2]),
        ("modern_hanok", get_scene_plans(60)[4]),
        ("factory", get_scene_plans(60)[3]),
    ]

    for subtype, scene in samples:
        duration_seconds = 30 if scene.scene_id <= 3 else 60
        prompt = make_scene_video_prompt(
            scene.scene_id,
            subtype,
            duration_seconds=duration_seconds,
            scene_plan=scene,
        )
        lowered = prompt.lower()
        assert ARCHITECTURE_SUBTYPES[subtype]["label"].lower() in lowered
        for material in ARCHITECTURE_SUBTYPES[subtype]["materials"]:
            assert material.lower() in lowered
        for color in ARCHITECTURE_SUBTYPES[subtype]["color_palette"]["primary"]:
            assert color.lower() in lowered
        assert prompt.count("Negative Prompt:") == 1
        assert prompt.rstrip().endswith(ARCH_NEGATIVE_BASE)


def test_factory_prompts_do_not_force_hanok_identity() -> None:
    factory_scene = get_scene_plans(60)[3]
    first_frame = make_first_frame_prompt("factory")
    prompt = make_scene_video_prompt(
        factory_scene.scene_id,
        "factory",
        duration_seconds=60,
        scene_plan=factory_scene,
    )

    lowered_first_frame = first_frame.lower()
    lowered_prompt = prompt.lower()
    assert "architecture subtype: factory" in lowered_first_frame
    assert "steel trusses" in lowered_first_frame
    assert "safety orange" in lowered_first_frame
    assert "hanok" not in lowered_first_frame

    assert "architecture subtype: factory" in lowered_prompt
    assert "steel trusses" in lowered_prompt
    assert "corrugated metal siding" in lowered_prompt
    assert "safety orange" in lowered_prompt
    assert "hanok" not in lowered_prompt
    assert "korean architecture subtype" not in lowered_prompt


def test_negative_prompt_suffix_is_single_and_terminal() -> None:
    prompt = make_scene_video_prompt(
        1,
        "dolmen",
        duration_seconds=30,
        scene_plan=get_scene_plans(30)[0],
    )

    assert prompt.count("Negative Prompt:") == 1
    assert prompt.rstrip().endswith(ARCH_NEGATIVE_BASE)
