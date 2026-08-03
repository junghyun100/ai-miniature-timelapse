"""
Tests for profile implementations (Section 21.2).

Each profile test verifies:
- Subtype registry traces to reference prompt
- Scene plan: start_state, ordered_actions, end_state, forbidden_changes
- Identity lock string present in prompts
- Style bible values match reference prompt tables
- Audio contract and negative prompt base
"""

import src.profiles.vehicle as vehicle_module
from src.profile_types import PROFILE_REGISTRY
from src.profiles import (
    architecture_profile,
    home_decor_profile,
)
from src.profiles.architecture import (
    ARCHITECTURE_SUBTYPES,
    get_scene_plans,
    make_first_frame_prompt,
    make_scene_video_prompt,
    make_style_bible,
)
from src.profiles.cooking import (
    KOREAN_DISHES,
    get_available_dishes,
)
from src.profiles.cooking import (
    make_first_frame_prompt as cooking_make_first,
)
from src.profiles.cooking import (
    make_scene_video_prompt as cooking_make_video,
)
from src.profiles.cooking import (
    make_style_bible as cooking_make_style_bible,
)
from src.profiles.home_decor import (
    make_scene_video_prompt as hd_make_video,
)
from src.profiles.home_decor import (
    make_style_bible as hd_make_style_bible,
)
from src.profiles.vehicle import (
    VehicleCategory,
    get_categories,
    get_models_for_category,
)
from src.profiles.vehicle import (
    make_first_frame_prompt as vehicle_make_first_frame,
)
from src.profiles.vehicle import (
    make_scene_video_prompt as vehicle_make_video,
)
from src.profiles.vehicle import (
    make_style_bible as vehicle_make_style_bible,
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
        """All architecture subtypes present across Korean and broader UI variants."""
        expected = {
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
        assert set(ARCHITECTURE_SUBTYPES.keys()) == expected

    def test_hanok_subtype_materials(self):
        hanok = ARCHITECTURE_SUBTYPES["hanok"]
        assert "wood" in hanok["materials"]
        assert "clay tiles (giwa)" in hanok["materials"] or "giwa" in str(hanok["materials"])
        assert "stone foundation" in hanok["materials"]

    def test_scene_plans_30s(self):
        plans = get_scene_plans(30)
        assert len(plans) == 3
        assert [plan.name for plan in plans] == [
            "Foundation & Walls",
            "Roofing & Exterior",
            "Painting & Landscaping Reveal",
        ]
        assert plans[0].scene_id == 1
        assert plans[0].input_mode.value == "MASTER_IMAGE"
        assert plans[1].input_mode.value == "PREVIOUS_FINAL_FRAME"
        assert plans[2].input_mode.value == "PREVIOUS_FINAL_FRAME"

    def test_scene_plans_60s(self):
        plans = get_scene_plans(60)
        assert len(plans) == 6
        assert [plan.name for plan in plans] == [
            "Foundation",
            "Wall & Windows",
            "Roofing",
            "Exterior",
            "Painting",
            "Landscaping & Reveal",
        ]

    def test_style_bible_identity_lock(self):
        sb = make_style_bible("hanok")
        # Architecture identity lock is now subtype-specific rather than fixed to hanok.
        assert "macro cinematography" in sb.identity_lock
        assert "100mm lens" in sb.identity_lock
        assert "hanok" in sb.identity_lock.lower()

    def test_factory_style_bible_and_prompt_stay_factory_specific(self):
        sb = make_style_bible("factory")
        assert "factory" in sb.identity_lock.lower()
        assert "hanok" not in sb.identity_lock.lower()
        assert "steel trusses" in sb.identity_lock.lower()
        assert "safety orange" in sb.identity_lock.lower()

        prompt = make_first_frame_prompt("factory")
        lowered = prompt.lower()
        assert "architecture subtype: factory" in lowered
        assert "steel trusses" in lowered
        assert "corrugated metal siding" in lowered
        assert "safety orange" in lowered
        assert "hanok" not in lowered

    def test_first_frame_prompt_contains_identity_lock(self):
        prompt = make_first_frame_prompt("hanok")
        # Reference prompt first frame style
        assert "macro photography" in prompt.lower()
        assert "miniature construction site" in prompt.lower()
        assert "giant human" in prompt.lower()
        assert "8K" in prompt
        assert "shallow depth of field" in prompt.lower()

    def test_scene_1_video_prompt(self):
        prompt = make_scene_video_prompt(1, "hanok")
        # Reference prompt scene 1: foundation
        assert "foundation" in prompt.lower()
        assert "ultra fast timelapse" in prompt.lower()
        assert "giant human" in prompt.lower() or "human hands" in prompt.lower()
        assert "Architecture subtype: Hanok" in prompt
        assert "clay tiles (giwa)" in prompt

    def test_scene_2_video_prompt(self):
        prompt = make_scene_video_prompt(2, "hanok")
        # Reference prompt scene 2: wall & windows / roofing
        assert "ultra fast timelapse" in prompt.lower()
        assert "giant human" in prompt.lower() or "human hands" in prompt.lower()

    def test_scene_3_video_prompt_30s(self):
        prompt = make_scene_video_prompt(3, "hanok")
        # Reference prompt scene 3: painting & landscaping reveal
        assert "ultra fast timelapse" in prompt.lower()
        assert "normal cinematic speed" in prompt.lower() or "cinematic" in prompt.lower()

    def test_negative_prompt_base(self):
        # Reference prompt negative (exact match)
        assert "text" in architecture_profile.negative_prompt_base
        assert "subtitle" in architecture_profile.negative_prompt_base
        assert "bad anatomy" in architecture_profile.negative_prompt_base
        assert "deformed hands" in architecture_profile.negative_prompt_base
        assert "blurry" in architecture_profile.negative_prompt_base


class TestVehicleProfile:
    """Test vehicle.assembly profile (Section 13.6)."""

    def test_profile_registered(self):
        assert "vehicle.assembly" in PROFILE_REGISTRY
        profile = PROFILE_REGISTRY["vehicle.assembly"]
        assert profile.workflow_mode.value == "REFERENCE_FRAME_RELAY"
        # REFERENCE_FRAME_RELAY supports 30s (3 scenes) and 60s (6 scenes) per spec
        assert profile.allowed_total_durations == [30, 60]
        assert profile.clip_duration_seconds == 10

    def test_categories(self):
        cats = get_categories()
        expected = {
            "car",
            "motorcycle",
            "airplane",
            "boat",
            "agricultural",
            "helicopter",
            "construction",
            "spaceship",
            "tank",
            "bicycle",
        }
        assert set(cats) == expected

    def test_models_for_car(self):
        models = get_models_for_category("car")
        assert "Porsche 911" in models
        assert "Ford Mustang" in models

    def test_style_bible_identity_lock(self):
        # make_style_bible(category, model_name) - needs both, category is VehicleCategory enum
        sb = vehicle_make_style_bible(VehicleCategory.CAR, "Porsche 911")
        # Vehicle profile uses per-category identity locks, not the product-style "hyper-realistic macro ASMR"
        assert "One coherent miniature car" in sb.identity_lock
        assert "unchanged wheelbase" in sb.identity_lock
        assert "giant_hands_with_tools" in sb.hands_rule

    def test_first_frame_prompt(self):
        prompt = vehicle_make_first_frame(VehicleCategory.CAR, "Porsche 911")
        assert "disassembled" in prompt.lower()
        assert "Porsche 911" in prompt
        assert "Master Image" in prompt
        assert "85mm lens" in prompt

    def test_video_prompt_cleanup_rule(self):
        # make_scene_video_prompt(category, model_name, scene_id, scene_name) - category is VehicleCategory
        prompt = vehicle_make_video(VehicleCategory.CAR, "Porsche 911", 1, "Foundation & Chassis")
        assert "visible edge staging tray" in prompt
        assert "visible hand contact" in prompt
        assert "installed parts remain fixed" in prompt
        assert "fully assembled car model" not in prompt.lower()
        assert "Negative Prompt:" in prompt

    def test_scene_1_is_non_final_and_scene_bounded(self):
        """Scene 1 should stop early and keep later vehicle stages reserved."""
        profile = PROFILE_REGISTRY["vehicle.assembly"]
        scene1 = profile.scene_plans[0]

        assert scene1.is_final_scene is False
        assert scene1.completion_range
        assert scene1.exact_stop_state.startswith(
            "Exact stop state after this scene's completed actions:"
        )
        assert "visibly incomplete" in scene1.exact_stop_state.lower()
        assert "fully assembled" not in scene1.exact_stop_state.lower()
        assert "clean workbench" not in scene1.exact_stop_state.lower()
        assert "final reveal" not in scene1.exact_stop_state.lower()
        assert scene1.reserved_future_actions
        assert "Engine block placed into chassis with precision" in scene1.ordered_actions
        assert "engine mounts secured" in scene1.ordered_actions

        vehicle_module.summarizeVehicleActions = lambda actions: "; ".join(actions)
        prompt = vehicle_make_video(
            VehicleCategory.CAR, "Porsche 911", scene1.scene_id, scene1.name
        )
        assert "exact stop" in prompt.lower()
        assert "visibly incomplete" in prompt.lower()
        assert "wheels and suspension mounted" not in prompt.lower()
        assert "do not invent work or begin a later stage" in prompt.lower()
        assert "fully assembled model" not in prompt.lower()
        assert "clean workbench" not in prompt.lower()
        assert "final reveal" not in prompt.lower()
        assert "Negative Prompt:" in prompt

    def test_final_scene_is_complete_and_reveals_finish(self):
        """Final vehicle scene should allow completion language and cleanup."""
        profile = PROFILE_REGISTRY["vehicle.assembly"]
        final_scene = profile.scene_plans[-1]

        assert final_scene.is_final_scene is True
        assert final_scene.completion_range
        assert final_scene.exact_stop_state
        assert "fully assembled" in final_scene.exact_stop_state.lower()
        assert "clean workbench" in final_scene.exact_stop_state.lower()

        vehicle_module.summarizeVehicleActions = lambda actions: "; ".join(actions)
        prompt = vehicle_make_video(
            VehicleCategory.CAR, "Porsche 911", final_scene.scene_id, final_scene.name
        )
        assert "fully assembled car model" in prompt.lower()
        assert "clean workbench" in prompt.lower()
        assert "final reveal" in prompt.lower()
        assert "Negative Prompt:" in prompt


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
            final_object="Traditional Lotus Mood Lamp",
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
        assert "raw ingredients" in prompt.lower()
        assert "cutting board" in prompt.lower()
        assert "hands only" in prompt.lower() or "only hands" in prompt.lower()
        assert "ASMR-rich" in prompt or "ASMR" in prompt

    def test_scene_1_preparation(self):
        prompt = cooking_make_video(1, "kimchi_jjigae")
        assert "washing" in prompt.lower()
        assert "slicing" in prompt.lower()
        assert "cubing" in prompt.lower() or "cubing" in prompt.lower()

    def test_scene_2_cooking(self):
        prompt = cooking_make_video(2, "kimchi_jjigae")
        assert "cooked" in prompt.lower()
        assert "all finishing materials visible and untouched" in prompt.lower()
        assert "reserved next-stage actions" not in prompt.lower()
        assert "do not advance beyond the current cooking stage" in prompt.lower()
        assert "hero" not in prompt.lower()
        assert "plating" not in prompt.lower()
        assert "plated" not in prompt.lower()
        assert "reveal" not in prompt.lower()

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

    def test_five_profiles_registered(self):
        assert len(PROFILE_REGISTRY) == 5
        expected = {
            "architecture.korean",
            "vehicle.assembly",
            "product.assembly",
            "home_decor.diy",
            "cooking.miniature",
        }
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
