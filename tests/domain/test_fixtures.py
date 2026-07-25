import json
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def load_fixture(name: str) -> dict:
    path = FIXTURES_DIR / name
    with open(path) as f:
        return json.load(f)


class TestDomain:
    def test_load_architecture_hanok_30(self):
        fixture = load_fixture("architecture-hanok-30-local.json")
        assert fixture["schema_version"] == "2.0"
        assert fixture["profile_id"] == "architecture.korean"
        assert fixture["workflow_mode"] == "REFERENCE_FRAME_RELAY"
        assert fixture["duration_seconds"] == 30
        assert len(fixture["scene_plans"]) == 3

    def test_load_architecture_hanok_60(self):
        fixture = load_fixture("architecture-hanok-60-local.json")
        assert fixture["duration_seconds"] == 60
        assert len(fixture["scene_plans"]) == 6

    def test_load_vehicle_car_10(self):
        fixture = load_fixture("vehicle-car-10-local.json")
        assert fixture["profile_id"] == "vehicle.assembly"
        assert fixture["workflow_mode"] == "SINGLE_CLIP_FROM_MASTER"
        assert fixture["duration_seconds"] == 10
        assert fixture["model_name"] == "Porsche 911"

    def test_load_vehicle_airplane_10(self):
        fixture = load_fixture("vehicle-airplane-10-local.json")
        assert fixture["subtype"] == "airplane"
        assert fixture["model_name"] == "Spitfire Mk IX"

    def test_load_home_decor_hanji_10(self):
        fixture = load_fixture("home-decor-hanji-10-local.json")
        assert fixture["profile_id"] == "home_decor.diy"
        assert "korean_narration" in fixture.get("derived_fields", {})
        assert fixture["duration_seconds"] == 10

    def test_load_cooking_kimchi_jjigae_30(self):
        fixture = load_fixture("cooking-kimchi-jjigae-30-local.json")
        assert fixture["profile_id"] == "cooking.miniature"
        assert fixture["workflow_mode"] == "REFERENCE_FRAME_RELAY"
        assert fixture["duration_seconds"] == 30
        assert fixture["dish_name"] == "Kimchi Jjigae"

    def test_load_nim_request_valid(self):
        fixture = load_fixture("nim-request-valid.json")
        assert fixture["schema_version"] == "2.0"
        assert "request_id" in fixture
        assert "source_revision" in fixture
        assert len(fixture["scenes"]) == 3
        assert fixture["scenes"][0]["local_first_frame_prompt"] != ""
        assert fixture["scenes"][1]["local_first_frame_prompt"] == ""
        assert fixture["scenes"][2]["local_first_frame_prompt"] == ""

    def test_load_nim_response_valid(self):
        fixture = load_fixture("nim-response-valid.json")
        assert fixture["schema_version"] == "2.0"
        assert "request_id" in fixture
        assert "source_revision" in fixture
        assert len(fixture["scenes"]) == 3
        assert fixture["scenes"][0]["first_frame_prompt"] != ""
        assert fixture["scenes"][1]["first_frame_prompt"] == ""
        assert fixture["scenes"][2]["first_frame_prompt"] == ""