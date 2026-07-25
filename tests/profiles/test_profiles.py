"""
Tests for profile implementations (Section 21.2).

Each profile test verifies:
- Subtype registry traces to reference prompt
- Scene plan: start_state, ordered_actions, end_state, forbidden_changes
- Identity lock string present in prompts
- Style bible values match reference prompt tables
- Audio contract and negative prompt base
"""
import pytest

from src.profile_types import PROFILE_REGISTRY
from src.profiles import (
    architecture_profile,
    vehicle_profile,
    home_decor_profile,
    cooking_profile,
)
from src.profiles.architecture import (
    ARCHITECTURE_SUBTYPES,
    make_style_bible,
    make_first_frame_prompt,
    make_scene_video_prompt,
    get_scene_plans,
)
from src.profiles.vehicle import (
    VEHICLE_MODELS,
    VehicleSubtype,
    make_style_bible as vehicle_make_style_bible,
    make_first_frame_prompt as vehicle_make_first_frame,
    make_scene_video_prompt as vehicle_make_video,
    get_categories,
    get_models_for_category,
)
from src.profiles.home_decor import (
    make_style_bible as hd_make_style_bible,
    make_scene_video_prompt as hd_make_video,
)
from src.profiles.cooking import (
    KOREAN_DISHES,
    make_style_bible as cooking_make_style_bible,
    make_first_frame_prompt as cooking_make_first,
    make_scene_video_prompt as cooking_make_video,
    get_available_dishes,
)


class TestArchitectureProfile:
    """Test architecture.korean profile (Section 13.5)."""

    def test_profile_registered(self):
        assert "architecture.korean" in PROFILE_REGISTRY
        profile = PROFILE_REGISTRY["architecture.korean"]
        assert profile.workflow_mode.value == "REFERENCE_FRAME_RELAY"
        assert profile.allowed_total_durations == [30, 60]
        assert profile.clip_duration_seconds == 10

    def test_subtype_registry(self):
        """All 6 subtypes from Table 13.5 present."""
        expected = {"hanok", "palace", "temple", "seowon", "modern_hanok", "dolmen"}
        assert set(ARCHITECTURE_SUBTYPES.keys()) == expected

    def test_hanok_subtype_materials(self):
        hanok = ARCHITECTURE_SUBTYPES["hanok"]
        assert "wood" in hanok["materials"]
        assert "clay tiles (giwa)" in hanok["materials"] or "giwa" in str(hanok["materials"])
        assert "stone foundation" in hanok["materials"]

    def test_scene_plans_30s(self):
        plans = get_scene_plans(30)
        assert len(plans) == 3
        assert plans[0].scene_id == 1
        assert plans[0].input_mode.value == "MASTER_IMAGE"
        assert plans[1].input_mode.value == "PREVIOUS_FINAL_FRAME"
        assert plans[2].input_mode.value == "PREVIOUS_FINAL_FRAME"

    def test_scene_plans_60s(self):
        plans = get_scene_plans(60)
        assert len(plans) == 6

    def test_style_bible_identity_lock(self):
        sb = make_style_bible("hanok")
        assert "macro cinematography" in sb.identity_lock
        assert "100mm lens" in sb.identity_lock
        assert "hanok" in sb.identity_lock.lower()

    def test_first_frame_prompt_contains_identity_lock(self):
        prompt = make_first_frame_prompt("hanok")
        assert "macro cinematography" in prompt
        assert "100mm macro lens" in prompt
        assert "Giants human hands only" in prompt or "giant human hands only" in prompt.lower()

    def test_scene_1_video_prompt(self):
        prompt = make_scene_video_prompt(1, "hanok")
        assert "Foundation" in prompt or "foundation" in prompt.lower()
        assert "mortise-and-tenon" in prompt.lower() or "mortise" in prompt.lower()

    def test_scene_2_video_prompt(self):
        prompt = make_scene_video_prompt(2, "hanok")
        assert "rafter" in prompt.lower() or "Rafter" in prompt
        assert "clay tiles" in prompt.lower() or "tiles" in prompt.lower()

    def test_scene_3_video_prompt_30s(self):
        prompt = make_scene_video_prompt(3, "hanok")
        assert "hanji" in prompt.lower() or "Dancheong" in prompt or "dancheong" in prompt.lower()

    def test_negative_prompt_base(self):
        assert "text" in architecture_profile.negative_prompt_base
        assert "miniature people" in architecture_profile.negative_prompt_base
        assert "steel" in architecture_profile.negative_prompt_base
        assert "concrete" in architecture_profile.negative_prompt_base


class TestVehicleProfile:
    """Test vehicle.assembly profile (Section 13.6)."""

    def test_profile_registered(self):
        assert "vehicle.assembly" in PROFILE_REGISTRY
        profile = PROFILE_REGISTRY["vehicle.assembly"]
        assert profile.workflow_mode.value == "SINGLE_CLIP_FROM_MASTER"
        assert profile.allowed_total_durations == [10]
        assert profile.clip_duration_seconds == 10

    def test_categories(self):
        cats = get_categories()
        expected = {"car", "motorcycle", "airplane", "boat", "agricultural",
                    "helicopter", "construction", "spaceship", "tank", "bicycle"}
        assert set(cats) == expected

    def test_models_for_car(self):
        models = get_models_for_category("car")
        assert "Porsche 911" in models
        assert "Ford Mustang" in models

    def test_style_bible_identity_lock(self):
        sb = vehicle_make_style_bible("Porsche 911", "car")
        assert "hyper-realistic macro ASMR assembly timelapse" in sb.identity_lock
        assert "giant human hands only" in sb.identity_lock.lower()
        assert "100% disassembled" in sb.identity_lock

    def test_first_frame_prompt(self):
        prompt = vehicle_make_first_frame("car", "Porsche 911")
        assert "disassembled" in prompt.lower()
        assert "Porsche 911" in prompt
        assert "Master Image" in prompt
        assert "85mm lens" in prompt

    def test_video_prompt_cleanup_rule(self):
        prompt = vehicle_make_video("car", "Porsche 911")
        assert "disappear from the workbench" in prompt
        assert "clean, leaving only the fully assembled model" in prompt
        assert "Negative Prompt:" in prompt

    def test_6_stage_assembly(self):
        """Test that assembly stages are reflected in scene plan ordered_actions."""
        profile = PROFILE_REGISTRY["vehicle.assembly"]
        ordered_actions = profile.scene_plans[0].ordered_actions
        # Check the 6-stage assembly is in scene plan (per Section 13.6)
        assert "Engine/chassis placed on workbench" in ordered_actions
        assert "Major sub-assemblies built (engine, drivetrain, suspension)" in ordered_actions
        assert "Sub-assemblies joined to chassis" in ordered_actions
        assert "Wheels/tracks/landing gear attached" in ordered_actions
        assert "Body panels/skin installed" in ordered_actions
        assert "Final detailing and cleanup" in ordered_actions


class TestHomeDecorProfile:
    """Test home_decor.diy profile (Section 13.8)."""

    def test_profile_registered(self):
        assert "home_decor.diy" in PROFILE_REGISTRY
        profile = PROFILE_REGISTRY["home_decor.diy"]
        assert profile.workflow_mode.value == "SINGLE_CLIP_FROM_MASTER"
        assert profile.allowed_total_durations == [10]
        assert profile.clip_duration_seconds == 10

    def test_audio_contract_korean_narration(self):
        profile = PROFILE_REGISTRY["home_decor.diy"]
        assert profile.audio_contract["type"] == "korean_narration_plus_asmr"

    def test_style_bible_identity_lock(self):
        sb = hd_make_style_bible("Traditional Lotus Mood Lamp", ["hanji", "plastic spoon"])
        assert "tactile mixed-media papercraft" in sb.identity_lock
        assert "3D layered paper-cutting" in sb.identity_lock
        assert "origami folding" in sb.identity_lock
        assert "top-down perspective" in sb.identity_lock
        assert "9:16 vertical" in sb.identity_lock

    def test_single_scene_plan(self):
        plans = home_decor_profile.scene_plans
        assert len(plans) == 1
        assert plans[0].scene_id == 1
        assert plans[0].input_mode.value == "MASTER_IMAGE"

    def test_video_prompt_structure(self):
        prompt = hd_make_video(
            craft_name="Traditional Lotus Mood Lamp",
            korean_narration="버려진 숟가락이 연꽃이 되다니 손으로 접으니 피어나네요",
            materials=["hanji", "plastic spoon", "wire", "glue"],
            final_object="Traditional Lotus Mood Lamp"
        )
        assert "Opening Hook" in prompt
        assert "Introducing Materials" in prompt
        assert "Building Begins" in prompt
        assert "Mid-Build Sequence" in prompt
        assert "Detail Showcase" in prompt
        assert "Final Reveal" in prompt
        assert "korean_narration" not in prompt  # placeholder replaced
        assert "버려진 숟가락이 연꽃이 되다니" in prompt
        assert "tactile mixed-media papercraft" in prompt
        assert "Negative Prompt:" in prompt


class TestCookingProfile:
    """Test cooking.miniature profile (Section 13.9)."""

    def test_profile_registered(self):
        assert "cooking.miniature" in PROFILE_REGISTRY
        profile = PROFILE_REGISTRY["cooking.miniature"]
        assert profile.workflow_mode.value == "REFERENCE_FRAME_RELAY"
        assert profile.allowed_total_durations == [30]
        assert profile.clip_duration_seconds == 10
        assert len(profile.scene_plans) == 3

    def test_dishes_available(self):
        dishes = get_available_dishes()
        assert "kimchi_jjigae" in dishes
        assert "bibimbap" in dishes
        assert "bulgogi" in dishes
        assert dishes["kimchi_jjigae"] == "Kimchi Jjigae"

    def test_kimchi_jjigae_materials(self):
        dish = KOREAN_DISHES["kimchi_jjigae"]
        assert "kimchi" in dish["ingredients"]
        assert "pork belly" in dish["ingredients"]
        assert "tofu" in dish["ingredients"]
        assert "ttukbaegi" in dish["cookware"] or "earthenware" in dish["cookware"]

    def test_style_bible_identity_lock(self):
        sb = cooking_make_style_bible("kimchi_jjigae")
        assert "ultra-realistic 8K HDR macro" in sb.identity_lock
        assert "100mm macro lens" in sb.identity_lock
        assert "giant human hands only" in sb.identity_lock.lower()
        assert "no miniature people" in sb.identity_lock.lower()
        assert "no tiny chef" in sb.identity_lock.lower()

    def test_first_frame_prompt(self):
        prompt = cooking_make_first("kimchi_jjigae")
        assert "Kimchi Jjigae" in prompt
        assert "cutting board" in prompt.lower()
        assert "miniature prep bowls" in prompt.lower()
        assert "ASMR-rich" in prompt or "ASMR" in prompt

    def test_scene_1_preparation(self):
        prompt = cooking_make_video(1, "kimchi_jjigae")
        assert "washing" in prompt.lower()
        assert "slicing" in prompt.lower()
        assert "cubing" in prompt.lower() or "cubing" in prompt.lower()

    def test_scene_2_cooking(self):
        prompt = cooking_make_video(2, "kimchi_jjigae")
        assert "heating oil" in prompt.lower() or "oil shimmer" in prompt.lower()
        assert "stir" in prompt.lower() or "melding" in prompt.lower()
        assert "simmer" in prompt.lower() or "boil" in prompt.lower()

    def test_scene_3_finishing(self):
        prompt = cooking_make_video(3, "kimchi_jjigae")
        assert "ladl" in prompt.lower() or "ladling" in prompt.lower()
        assert "garnish" in prompt.lower()
        assert "hero" in prompt.lower() or "cinematic hero" in prompt.lower()
        assert "steam rising" in prompt.lower() or "steam" in prompt.lower()

    def test_audio_contract_asmr_only(self):
        profile = PROFILE_REGISTRY["cooking.miniature"]
        assert profile.audio_contract["type"] == "asmr_only"
        desc = profile.audio_contract["description"].lower()
        assert "voice" not in desc or "no voices" in desc
        assert "music" not in desc or "no music" in desc


class TestProfileRegistry:
    """Test all profiles are registered."""

    def test_four_profiles_registered(self):
        assert len(PROFILE_REGISTRY) == 4
        expected = {"architecture.korean", "vehicle.assembly", "home_decor.diy", "cooking.miniature"}
        assert set(PROFILE_REGISTRY.keys()) == expected

    def test_all_have_required_fields(self):
        for profile in PROFILE_REGISTRY.values():
            assert profile.profile_id
            assert profile.version
            assert profile.topic_label
            assert profile.workflow_mode
            assert profile.allowed_total_durations
            assert profile.clip_duration_seconds > 0
            assert profile.scene_plans
            assert profile.selection_schema
            assert profile.negative_prompt_base
            assert profile.template_exclusions is not None