"""Tests for UI vehicle scene boundaries and phase transitions."""

import pytest

from src.profiles.vehicle import VEHICLE_MODELS, VEHICLE_IDENTITY_LOCKS, VEHICLE_KEY_PARTS


def test_vehicle_categories_count():
    """Test that we have 10 vehicle categories."""
    from src.profiles.vehicle import get_categories
    categories = get_categories()
    assert len(categories) == 10
    expected = {"car", "motorcycle", "airplane", "boat", "agricultural",
                "helicopter", "construction", "spaceship", "tank", "bicycle"}
    assert set(categories) == expected


def test_vehicle_models_per_category():
    """Test that each category has exactly 10 models."""
    from src.profiles.vehicle import VEHICLE_MODELS
    for cat, models in VEHICLE_MODELS.items():
        assert len(models) == 10, f"Category {cat} should have 10 models"


def test_scene_plans_30s_and_60s():
    """Test that build_scene_plans_30s and 60s work."""
    from src.profiles.vehicle import build_scene_plans_30s, build_scene_plans_60s
    plans_30 = build_scene_plans_30s("car")
    plans_60 = build_scene_plans_60s("car")
    assert len(plans_30) == 3  # 30s / 10s per clip = 3 scenes
    assert len(plans_60) == 6  # 60s / 10s per clip = 6 scenes


def test_identity_locks_exist():
    """Test that identity locks exist for all categories."""
    from src.profiles.vehicle import VEHICLE_IDENTITY_LOCKS
    for cat in VEHICLE_MODELS.keys():
        assert cat in VEHICLE_IDENTITY_LOCKS
        assert len(VEHICLE_IDENTITY_LOCKS[cat]) > 0


def test_key_parts_exist():
    """Test that key parts exist for all categories."""
    from src.profiles.vehicle import VEHICLE_KEY_PARTS
    for cat in VEHICLE_MODELS.keys():
        assert cat in VEHICLE_KEY_PARTS
        assert len(VEHICLE_KEY_PARTS[cat]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])