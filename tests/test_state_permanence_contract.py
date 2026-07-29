from __future__ import annotations

from src.domain import AssetKind, AssetRef, AssetScope, InputMode, Scene
from src.profile_types import STATE_PERMANENCE_RULE
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
    assert "exact stop state" in lowered
    assert "keep every already-installed" in lowered
    assert STATE_PERMANENCE_RULE in lowered


def test_vehicle_video_prompt_carries_state_permanence():
    prompt = vehicle_video_prompt(VehicleCategory.CAR, "Porsche 911", 1, "Foundation & Chassis", total_duration=30)

    lowered = prompt.lower()
    assert "keep every already-installed" in lowered
    assert "must remain visibly incomplete" in lowered


def test_product_video_prompt_carries_state_permanence():
    prompt = product_video_prompt(1, "watch", 30)

    lowered = prompt.lower()
    assert "keep every already-installed" in lowered
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
