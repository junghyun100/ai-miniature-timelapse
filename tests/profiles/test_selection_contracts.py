from __future__ import annotations

import json

from src.profile_types import (
    PROFILE_REGISTRY,
    WorkflowMode,
    load_all_profiles,
    profile_to_dict,
    profile_to_json,
)

PROFILE_IDS = {
    "architecture.korean",
    "vehicle.assembly",
    "product.assembly",
    "home_decor.diy",
    "cooking.miniature",
}

EXPECTED_DURATIONS = {
    "architecture.korean": [30, 60],
    "vehicle.assembly": [30, 60],
    "product.assembly": [10, 30, 60],
    "home_decor.diy": [10],
    "cooking.miniature": [30],
}


def _profiles():
    load_all_profiles()
    return [PROFILE_REGISTRY[profile_id] for profile_id in sorted(PROFILE_IDS)]


def test_all_five_profiles_register_and_use_normalized_selection_schemas() -> None:
    profiles = _profiles()

    assert PROFILE_IDS.issubset(PROFILE_REGISTRY)
    for profile in profiles:
        schema = profile.selection_schema
        assert schema["type"] == "object"
        assert schema["title"]
        assert isinstance(schema["required"], list)
        assert isinstance(schema["properties"], dict)
        assert schema["x-ui-order"] == list(schema["properties"])
        assert set(schema["required"]).issubset(schema["properties"])
        assert "duration_seconds" not in schema["properties"]

        for field in schema["properties"].values():
            assert field["title"]
            if "enum" in field:
                assert len(field["x-enum-labels"]) == len(field["enum"])


def test_duration_matrix_has_one_profile_source_of_truth() -> None:
    for profile in _profiles():
        assert profile.allowed_total_durations == EXPECTED_DURATIONS[profile.profile_id]
        assert profile.default_total_duration in profile.allowed_total_durations
        assert "duration_seconds" not in profile.selection_schema["properties"]


def test_vehicle_model_options_depend_on_vehicle_category() -> None:
    from src.profiles.vehicle import VEHICLE_MODELS, VehicleCategory, vehicle_profile

    dependency = vehicle_profile.selection_schema["properties"]["model_name"][
        "x-dependent-options"
    ]

    assert dependency["field"] == "vehicle_category"
    assert set(dependency["options"]) == {
        category.value for category in VehicleCategory
    }
    for category, models in VEHICLE_MODELS.items():
        assert dependency["options"][category.value] == models


def test_home_decor_narration_uses_60_non_whitespace_character_contract() -> None:
    from src.profiles.home_decor import (
        HOME_DECOR_NARRATION_MAX_NON_WHITESPACE,
        HOME_DECOR_SELECTION_SCHEMA,
        count_narration_characters,
        validate_korean_narration,
    )

    narration_schema = HOME_DECOR_SELECTION_SCHEMA["properties"]["korean_narration"]
    assert "maxLength" not in narration_schema
    assert narration_schema["x-length-contract"] == {
        "max": 60,
        "counting": "non-whitespace-characters",
    }
    assert HOME_DECOR_NARRATION_MAX_NON_WHITESPACE == 60
    assert count_narration_characters("가 나\n다\t라") == 4
    assert validate_korean_narration("가 " * 60)
    assert not validate_korean_narration("가" * 61)
    assert not validate_korean_narration(" \n\t")


def test_product_workflow_is_duration_aware_without_changing_legacy_enum() -> None:
    from src.profiles.product import product_profile

    assert product_profile.workflow_mode == WorkflowMode.SINGLE_CLIP_FROM_MASTER
    assert product_profile.get_workflow_mode(10) == WorkflowMode.SINGLE_CLIP_FROM_MASTER
    assert product_profile.get_workflow_mode(30) == WorkflowMode.REFERENCE_FRAME_RELAY
    assert product_profile.get_workflow_mode(60) == WorkflowMode.REFERENCE_FRAME_RELAY

    manifest = profile_to_dict(product_profile)
    assert manifest["workflow_mode"] == "SINGLE_CLIP_FROM_MASTER"
    assert manifest["workflow_mode_by_duration"] == {
        "10": "SINGLE_CLIP_FROM_MASTER",
        "30": "REFERENCE_FRAME_RELAY",
        "60": "REFERENCE_FRAME_RELAY",
    }


def test_profile_manifests_are_json_serializable_without_callables() -> None:
    for profile in _profiles():
        manifest = profile_to_dict(profile)
        payload = json.loads(profile_to_json(profile))

        assert payload == manifest
        assert json.dumps(manifest, ensure_ascii=False)
        assert isinstance(manifest["scene_plans_factory"], bool)
        assert isinstance(manifest["style_bible_factory"], bool)
        assert isinstance(manifest["first_frame_factory"], bool)
        assert isinstance(manifest["scene_prompt_factory"], bool)
