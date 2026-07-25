"""
Cooking Miniature Profile (cooking.miniature)

Per Section 13.9:
- Workflow: REFERENCE_FRAME_RELAY
- Duration: 30s (3 clips × 10s)
- Scenes: Preparation → Cooking → Finishing & Plating
- ASMR audio only (no voice, no music)
- Hands only (giant human hands)
- 100mm macro lens, ultra-realistic 8K HDR
"""

from ..profile_types import (
    Profile, ScenePlan, WorkflowMode, StyleBible, InputMode, register_profile
)


COOKING_IDENTITY_LOCK = (
    "ultra-realistic 8K HDR macro cinematography, 100mm macro lens, "
    "extreme close-up, soft focus pulls, giant human hands only, "
    "no miniature people, no tiny chef, no small person, all objects miniature "
    "except hands, all tools miniature, all ingredients miniature, "
    "identical kitchen, lighting, cutting board, stove, camera style throughout, "
    "physical realism: logical cooking steps never skipped, food reactions "
    "(sizzle, browning, steam) realistic"
)


COOKING_NEGATIVE_BASE = (
    "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, "
    "bad anatomy, deformed hands, blurry, miniature people, tiny chef, small person, "
    "shaky camera, camera shake, music, voice, narration, dialogue, talking"
)


KOREAN_DISHES = {
    "kimchi_jjigae": {
        "name": "Kimchi Jjigae",
        "ingredients": ["kimchi", "pork belly", "tofu", "green onion", "gochujang", "garlic"],
        "cookware": "miniature earthenware pot (ttukbaegi)",
        "heat_source": "tea light candle under pot",
        "garnish": "sesame oil drizzle, sliced green onion",
        "serveware": "miniature black stone bowl",
        "actions_prep": ["washing kimchi", "slicing pork belly", "cubing tofu", "chopping green onion", "mincing garlic"],
        "actions_cook": ["heating oil in pot", "stir-frying kimchi", "adding pork and browning", "pouring water and boiling", "adding tofu and green onion", "simmering until melded"],
        "actions_finish": ["ladling into stone bowl", "drizzling sesame oil", "sprinkling green onion", "hero shot with steam"],
    },
    "bibimbap": {
        "name": "Bibimbap",
        "ingredients": ["rice", "spinach", "bean sprouts", "carrot", "zucchini", "mushrooms", "gochujang", "egg", "beef"],
        "cookware": "miniature stone bowl (dolsot)",
        "heat_source": "tea light candle under bowl",
        "garnish": "sesame seeds, sesame oil, fried egg on top",
        "serveware": "miniature stone bowl",
        "actions_prep": ["cooking rice", "blanching spinach", "blanching bean sprouts", "julienning carrot and zucchini", "sautéing mushrooms", "cooking beef"],
        "actions_cook": ["heating stone bowl", "arranging vegetables on rice", "cracking egg on top", "adding gochujang", "sizzling rice crust forming"],
        "actions_finish": ["mixing gently", "hero shot with steam and egg yolk", "sesame oil drizzle"],
    },
    "bulgogi": {
        "name": "Bulgogi",
        "ingredients": ["thinly sliced beef", "soy sauce", "sugar", "garlic", "pear", "onion", "green onion", "sesame oil"],
        "cookware": "miniature cast iron grill pan",
        "heat_source": "tea light candle under pan",
        "garnish": "sesame seeds, green onion",
        "serveware": "miniature white porcelain plate",
        "actions_prep": ["slicing beef thinly", "grating pear and onion", "making marinade", "marinating beef", "chopping green onion"],
        "actions_cook": ["heating grill pan", "grilling marinated beef", "caramelization and char marks", "juices reducing"],
        "actions_finish": ["plating on porcelain", "sprinkling sesame seeds", "adding green onion", "hero shot with glistening beef"],
    },
    "jjajangmyeon": {
        "name": "Jjajangmyeon",
        "ingredients": ["noodles", "chunjang (black bean paste)", "pork", "onion", "zucchini", "potato", "cabbage"],
        "cookware": "miniature wok",
        "heat_source": "tea light candle under wok",
        "garnish": "cucumber julienne",
        "serveware": "miniature black bowl",
        "actions_prep": ["boiling noodles", "dicing pork and vegetables", "preparing chunjang"],
        "actions_cook": ["heating wok", "frying chunjang in oil", "stir-frying pork and vegetables", "adding water and simmering", "thickening with starch slurry"],
        "actions_finish": ["placing noodles in bowl", "pouring sauce over", "topping with cucumber", "hero shot mixing"],
    },
    "samgyeopsal": {
        "name": "Samgyeopsal (Grilled Pork Belly)",
        "ingredients": ["pork belly slices", "garlic", "green chili", "ssamjang", "lettuce", "perilla leaves", "kimchi"],
        "cookware": "miniature tabletop grill",
        "heat_source": "tea light candle under grill",
        "garnish": "grilled garlic and chili",
        "serveware": "miniature grill plate with lettuce wraps",
        "actions_prep": ["slicing pork belly", "preparing ssamjang", "washing lettuce and perilla", "slicing garlic and chili"],
        "actions_cook": ["heating grill", "laying pork belly slices", "flipping for even char", "grilling garlic and chili alongside", "fat rendering and sizzling"],
        "actions_finish": ["wrapping meat in lettuce with ssamjang", "adding grilled garlic/chili", "hero shot of wrap being eaten"],
    },
    "dakgalbi": {
        "name": "Dakgalbi (Spicy Stir-fried Chicken)",
        "ingredients": ["chicken thigh", "gochujang", "gochugaru", "sweet potato", "cabbage", "perilla leaves", "rice cakes", "cheese"],
        "cookware": "miniature wide pan",
        "heat_source": "tea light candle under pan",
        "garnish": "melted cheese, perilla leaves",
        "serveware": "miniature cast iron pan",
        "actions_prep": ["cutting chicken", "making spicy marinade", "marinating chicken", "slicing vegetables"],
        "actions_cook": ["heating pan", "stir-frying chicken", "adding vegetables and rice cakes", "sauce caramelizing", "cheese melting on top"],
        "actions_finish": ["hero shot with melted cheese pull", "perilla leaves on top", "steam rising"],
    },
}


# Scene plans for 30s (3 scenes × 10s)
SCENE_PLANS_30S = [
    ScenePlan(
        scene_id=1,
        name="Preparation",
        start_state="Empty cutting board, ingredients raw",
        ordered_actions=["washing", "slicing", "cubing", "chopping", "mincing", "arranging in prep bowls"],
        end_state="All ingredients prepped and arranged in miniature bowls, ready for cooking",
        forbidden_changes=[
            "Kitchen", "Lighting", "Cutting board", "Camera style", "Hand position"
        ],
        input_mode=InputMode.MASTER_IMAGE,
        estimated_clip_duration_seconds=10,
    ),
    ScenePlan(
        scene_id=2,
        name="Cooking",
        start_state="Ingredients ready, cookware on heat",
        ordered_actions=["heating oil/pan", "stir-frying aromatics", "adding protein", "adding liquid", "simmering/grilling", "ingredients melding"],
        end_state="Dish cooking, steam rising, bubbles/sizzle visible",
        forbidden_changes=[
            "Kitchen", "Lighting", "Cookware", "Heat source", "Camera style"
        ],
        input_mode=InputMode.PREVIOUS_FINAL_FRAME,
        estimated_clip_duration_seconds=10,
    ),
    ScenePlan(
        scene_id=3,
        name="Finishing & Plating",
        start_state="Dish cooked, ready for plating",
        ordered_actions=["ladling/plating", "adding garnish", "final drizzles", "hero close-up with steam"],
        end_state="Finished dish in serveware, cinematic hero shot with natural steam",
        forbidden_changes=[
            "Kitchen", "Lighting", "Serveware", "Camera style", "Cooking state continuity"
        ],
        input_mode=InputMode.PREVIOUS_FINAL_FRAME,
        estimated_clip_duration_seconds=10,
    ),
]


COOKING_SELECTION_SCHEMA = {
    "type": "object",
    "required": ["dish_key"],
    "properties": {
        "dish_key": {"type": "string", "enum": list(KOREAN_DISHES.keys())},
    },
}


cooking_profile = Profile(
    profile_id="cooking.miniature",
    version="2.0.0",
    topic_label="Miniature Cooking",
    workflow_mode=WorkflowMode.REFERENCE_FRAME_RELAY,
    allowed_total_durations=[30],
    default_total_duration=30,
    clip_duration_seconds=10,
    scene_plans=SCENE_PLANS_30S,
    scene_plans_factory=lambda topic, dur, ctx: SCENE_PLANS_30S,
    selection_schema=COOKING_SELECTION_SCHEMA,
    style_bible_factory=lambda topic, dur, ctx: make_style_bible(ctx["dish_key"]),
    first_frame_factory=lambda topic, dur, ctx: {"first_frame_prompt": make_first_frame_prompt(ctx["dish_key"])} if ctx.get("scene_id") == 1 else {},
    scene_prompt_factory=lambda topic, dur, ctx: {"video_prompt": make_scene_video_prompt(ctx["scene_id"], ctx["dish_key"])},
    audio_contract={
        "type": "asmr_only",
        "description": "Only satisfying ASMR sounds: knife chops, water drips, sizzle, boil, simmer, pour, drizzle, gentle clink. No voices, no music, no narration."
    },
    negative_prompt_base=COOKING_NEGATIVE_BASE,
    template_exclusions=["miniature people", "tiny chef", "voice", "music", "traditional kitchen tools (non-miniature)"],
)

register_profile(cooking_profile)


def make_style_bible(dish_key: str) -> StyleBible:
    dish = KOREAN_DISHES[dish_key]
    return StyleBible(
        identity_lock=COOKING_IDENTITY_LOCK,
        materials={
            "primary": dish["ingredients"],
            "secondary": [dish["cookware"], dish["heat_source"], dish["serveware"]],
            "tools": ["miniature knife", "miniature ladle", "miniature spatula", "miniature chopsticks", "miniature tongs"],
        },
        camera={
            "lens": "100mm macro",
            "angle": "extreme_closeup",
            "movement": "soft_focus_pull",
            "distance": "extreme_macro",
        },
        lighting={
            "key": "soft kitchen lighting",
            "fill": "warm candle glow from heat source",
            "mood": "warm_cinematic",
            "consistency": "locked",
        },
        color_palette={
            "primary": ["food-natural colors (reds, greens, whites, browns)"],
            "accent": ["steam", "oil sheen", "caramelization", "charring"],
            "background": "softly blurred modern kitchen",
            "tone": "warm_natural",
        },
        workspace={
            "surface": "natural wooden cutting board",
            "environment": "clean modern kitchen with softly blurred background",
            "clutter_rule": "organized_prep_then_clean",
        },
        hands_rule="giant_hands_only",
        motion_rule="asmr_prep",
        negative_prompt_base=COOKING_NEGATIVE_BASE,
    )


def make_first_frame_prompt(dish_key: str) -> str:
    dish = KOREAN_DISHES[dish_key]
    actions_preview = "; ".join(dish["actions_prep"][:3])
    return (
        f"Ultra-realistic 8K HDR macro cinematography, 100mm macro lens, extreme close-up, "
        f"soft focus pulls. Giant human hands only, no miniature people, preparing ingredients "
        f"for {dish['name']} on a natural wooden cutting board in a clean modern kitchen with "
        f"softly blurred background. {actions_preview} — every motion fluid and ASMR-rich "
        f"(knife chopping sounds, water drips). All ingredients neatly arranged in miniature "
        f"prep bowls, ready for cooking. Identical kitchen, lighting, cutting board, and hand "
        f"position carry into next scene. No voices, no music, only satisfying ASMR sounds. "
        f"Negative Prompt: {COOKING_NEGATIVE_BASE}."
    )


def make_scene_video_prompt(scene_id: int, dish_key: str) -> str:
    dish = KOREAN_DISHES[dish_key]

    if scene_id == 1:
        actions = "; ".join(dish["actions_prep"])
        return (
            f"Ultra-realistic 8K HDR macro cinematography, 100mm macro lens, extreme close-up, "
            f"soft focus pulls. Giant human hands only, no miniature people, preparing ingredients "
            f"for {dish['name']} on a natural wooden cutting board in a clean modern kitchen with "
            f"softly blurred background. {actions} — every motion fluid and ASMR-rich (knife "
            f"chopping sounds, water drips). All ingredients neatly arranged in miniature prep "
            f"bowls, ready for cooking. Identical kitchen, lighting, cutting board, and hand "
            f"position carry into next scene. No voices, no music, only satisfying ASMR sounds. "
            f"Negative Prompt: {COOKING_NEGATIVE_BASE}."
        )
    elif scene_id == 2:
        actions = "; ".join(dish["actions_cook"])
        return (
            f"Ultra-realistic 8K HDR macro cinematography, 100mm macro lens, extreme close-up, "
            f"seamless continuation from previous scene. Giant human hands only, same kitchen, "
            f"same wooden cutting board, same lighting, same camera. Hands transfer prepped "
            f"ingredients into {dish['cookware']} over {dish['heat_source']}. Realistic cooking "
            f"physics: oil shimmer, vigorous bubbling steam, browning Maillard reaction, reduction "
            f"of broth, ingredients melding — all captured in hypnotic extreme close-up with "
            f"authentic ASMR (sizzle, boil, simmer). Logical cooking sequence without skipped "
            f"steps. Identical environment carries into next scene. No voices, no music, only "
            f"satisfying ASMR sounds. Negative Prompt: {COOKING_NEGATIVE_BASE}."
        )
    else:
        actions = "; ".join(dish["actions_finish"])
        return (
            f"Ultra-realistic 8K HDR macro cinematography, 100mm macro lens, extreme close-up, "
            f"seamless continuation. Giant human hands only, same kitchen, same cookware, same "
            f"lighting. Hands ladle finished {dish['name']} into {dish['serveware']} using "
            f"miniature utensils. Delicate garnish: {dish['garnish']}. Final cinematic hero shot: "
            f"steam rising naturally, textures hyper-detailed (tofu pores, kimchi fibers, oil "
            f"sheen), focus pull to hero angle. Hands gently exit frame. Satisfying ASMR (pour, "
            f"drizzle, gentle clink). No voices, no music, only ASMR. Negative Prompt: "
            f"{COOKING_NEGATIVE_BASE}."
        )


def get_available_dishes() -> dict:
    return {k: v["name"] for k, v in KOREAN_DISHES.items()}