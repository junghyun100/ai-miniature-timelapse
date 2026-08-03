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
    STATE_PERMANENCE_RULE,
    InputMode,
    Profile,
    ScenePlan,
    StyleBible,
    WorkflowMode,
    append_scene_control_block,
    register_profile,
)

COOKING_IDENTITY_LOCK = (
    "ultra-realistic 8K HDR macro cinematography, 100mm macro lens, "
    "extreme close-up, soft focus pulls, giant human hands only, "
    "no miniature people, no tiny chef, no small person, all objects miniature "
    "except hands, all tools miniature, all ingredients miniature, "
    "identical kitchen, lighting, cutting board, stove, camera style throughout, "
    "physical realism: logical cooking steps never skipped, food reactions "
    "(sizzle, browning, steam) realistic, "
    f"{STATE_PERMANENCE_RULE}"
)


COOKING_NEGATIVE_BASE = (
    "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, "
    "bad anatomy, deformed hands, blurry, miniature people, tiny chef, small person, "
    "shaky camera, camera shake, music, voice, narration, dialogue, talking"
)

COOKING_CONTINUITY_LOCK = (
    "one uninterrupted locked composition, cumulative ingredient state, "
    "no alternate camera, no zoom or reframe during cooking, no completed-state jump, no ingredient-state loss, "
    "no morphing into a different dish, no rebuild from scratch"
)


COOKING_PREP_ACTIONS = [
    "washing ingredients",
    "sorting ingredients into prep bowls",
    "slicing and chopping",
    "cubing and trimming",
    "mincing aromatics",
    "arranging everything in order before heat begins",
]


COOKING_COOK_ACTIONS = [
    "heating oil in the cookware",
    "stir-frying aromatics",
    "adding the main ingredients",
    "pouring liquid and bringing it to a boil",
    "simmering until fully cooked",
    "keeping all finishing materials untouched",
]


COOKING_PLATING_ACTIONS = [
    "ladling the cooked dish into the serveware",
    "drizzling finishing oil",
    "sprinkling garnish",
    "revealing the steam presentation",
]


KOREAN_DISHES = {
    "kimchi_jjigae": {
        "name": "Kimchi Jjigae",
        "ingredients": ["kimchi", "pork belly", "tofu", "green onion", "gochujang", "garlic"],
        "cookware": "miniature earthenware pot (ttukbaegi)",
        "heat_source": "tea light candle under pot",
        "garnish": "sesame oil drizzle, sliced green onion",
        "serveware": "miniature black stone bowl",
        "actions_prep": [
            "washing kimchi",
            "slicing pork belly",
            "cubing tofu",
            "chopping green onion",
            "mincing garlic",
        ],
        "actions_cook": [
            "heating oil in pot",
            "stir-frying kimchi",
            "adding pork and browning",
            "pouring water and boiling",
            "adding tofu and green onion",
            "simmering until melded",
        ],
        "actions_finish": [
            "ladling into stone bowl",
            "drizzling sesame oil",
            "sprinkling green onion",
            "hero shot with steam",
        ],
    },
    "bibimbap": {
        "name": "Bibimbap",
        "ingredients": [
            "rice",
            "spinach",
            "bean sprouts",
            "carrot",
            "zucchini",
            "mushrooms",
            "gochujang",
            "egg",
            "beef",
        ],
        "cookware": "miniature stone bowl (dolsot)",
        "heat_source": "tea light candle under bowl",
        "garnish": "sesame seeds, sesame oil, fried egg on top",
        "serveware": "miniature stone bowl",
        "actions_prep": [
            "cooking rice",
            "blanching spinach",
            "blanching bean sprouts",
            "julienning carrot and zucchini",
            "sautéing mushrooms",
            "cooking beef",
        ],
        "actions_cook": [
            "heating stone bowl",
            "arranging vegetables on rice",
            "cracking egg on top",
            "adding gochujang",
            "sizzling rice crust forming",
        ],
        "actions_finish": [
            "mixing gently",
            "hero shot with steam and egg yolk",
            "sesame oil drizzle",
        ],
    },
    "bulgogi": {
        "name": "Bulgogi",
        "ingredients": [
            "thinly sliced beef",
            "soy sauce",
            "sugar",
            "garlic",
            "pear",
            "onion",
            "green onion",
            "sesame oil",
        ],
        "cookware": "miniature cast iron grill pan",
        "heat_source": "tea light candle under pan",
        "garnish": "sesame seeds, green onion",
        "serveware": "miniature white porcelain plate",
        "actions_prep": [
            "slicing beef thinly",
            "grating pear and onion",
            "making marinade",
            "marinating beef",
            "chopping green onion",
        ],
        "actions_cook": [
            "heating grill pan",
            "grilling marinated beef",
            "caramelization and char marks",
            "juices reducing",
        ],
        "actions_finish": [
            "plating on porcelain",
            "sprinkling sesame seeds",
            "adding green onion",
            "hero shot with glistening beef",
        ],
    },
    "jjajangmyeon": {
        "name": "Jjajangmyeon",
        "ingredients": [
            "noodles",
            "chunjang (black bean paste)",
            "pork",
            "onion",
            "zucchini",
            "potato",
            "cabbage",
        ],
        "cookware": "miniature wok",
        "heat_source": "tea light candle under wok",
        "garnish": "cucumber julienne",
        "serveware": "miniature black bowl",
        "actions_prep": ["boiling noodles", "dicing pork and vegetables", "preparing chunjang"],
        "actions_cook": [
            "heating wok",
            "frying chunjang in oil",
            "stir-frying pork and vegetables",
            "adding water and simmering",
            "thickening with starch slurry",
        ],
        "actions_finish": [
            "placing noodles in bowl",
            "pouring sauce over",
            "topping with cucumber",
            "hero shot mixing",
        ],
    },
    "samgyeopsal": {
        "name": "Samgyeopsal (Grilled Pork Belly)",
        "ingredients": [
            "pork belly slices",
            "garlic",
            "green chili",
            "ssamjang",
            "lettuce",
            "perilla leaves",
            "kimchi",
        ],
        "cookware": "miniature tabletop grill",
        "heat_source": "tea light candle under grill",
        "garnish": "grilled garlic and chili",
        "serveware": "miniature grill plate with lettuce wraps",
        "actions_prep": [
            "slicing pork belly",
            "preparing ssamjang",
            "washing lettuce and perilla",
            "slicing garlic and chili",
        ],
        "actions_cook": [
            "heating grill",
            "laying pork belly slices",
            "flipping for even char",
            "grilling garlic and chili alongside",
            "fat rendering and sizzling",
        ],
        "actions_finish": [
            "wrapping meat in lettuce with ssamjang",
            "adding grilled garlic/chili",
            "hero shot of wrap being eaten",
        ],
    },
    "dakgalbi": {
        "name": "Dakgalbi (Spicy Stir-fried Chicken)",
        "ingredients": [
            "chicken thigh",
            "gochujang",
            "gochugaru",
            "sweet potato",
            "cabbage",
            "perilla leaves",
            "rice cakes",
            "cheese",
        ],
        "cookware": "miniature wide pan",
        "heat_source": "tea light candle under pan",
        "garnish": "melted cheese, perilla leaves",
        "serveware": "miniature cast iron pan",
        "actions_prep": [
            "cutting chicken",
            "making spicy marinade",
            "marinating chicken",
            "slicing vegetables",
        ],
        "actions_cook": [
            "heating pan",
            "stir-frying chicken",
            "adding vegetables and rice cakes",
            "sauce caramelizing",
            "cheese melting on top",
        ],
        "actions_finish": [
            "hero shot with melted cheese pull",
            "perilla leaves on top",
            "steam rising",
        ],
    },
}


SCENE_1_PREP_STOP = (
    "All ingredients prepped and arranged in miniature bowls, ready for cooking. "
    "Raw ingredients stay visible and fixed. All prepped ingredients remain in place."
)
SCENE_2_COOK_STOP = (
    "Dish fully cooked with steam visible, all finishing materials visible and untouched in the edge prep tray. "
    "Prepared ingredients and cookware remain visible and fixed."
)
SCENE_3_FINAL_STOP = (
    "Finished plated dish in serveware with natural steam and hero reveal. "
    "Earlier prep and cooking elements remain visible and fixed."
)


def _future_action_block(actions: list[str]) -> tuple[list[str], list[str]]:
    reserved = list(actions)
    forbidden = [
        f"Do not perform this later-stage action in the current scene: {action}"
        for action in actions
    ]
    return reserved, forbidden


SCENE_1_RESERVED, SCENE_1_FORBIDDEN = _future_action_block(
    COOKING_COOK_ACTIONS + COOKING_PLATING_ACTIONS
)
SCENE_2_RESERVED, SCENE_2_FORBIDDEN = _future_action_block(COOKING_PLATING_ACTIONS)


# Scene plans for 30s (3 scenes × 10s)
SCENE_PLANS_30S = [
    ScenePlan(
        scene_id=1,
        name="Preparation",
        start_state="Raw ingredients only on the cutting board, before any heat or cookware is used",
        ordered_actions=COOKING_PREP_ACTIONS,
        end_state=SCENE_1_PREP_STOP,
        forbidden_changes=["Kitchen", "Lighting", "Cutting board", "Camera style", "Hand position"],
        input_mode=InputMode.MASTER_IMAGE,
        estimated_clip_duration_seconds=10,
        completion_range="0-35%",
        is_final_scene=False,
        reserved_future_actions=SCENE_1_RESERVED,
        forbidden_future_actions=SCENE_1_FORBIDDEN,
        exact_stop_state=SCENE_1_PREP_STOP,
    ),
    ScenePlan(
        scene_id=2,
        name="Cooking",
        start_state=SCENE_1_PREP_STOP,
        ordered_actions=COOKING_COOK_ACTIONS,
        end_state=SCENE_2_COOK_STOP,
        forbidden_changes=["Kitchen", "Lighting", "Cookware", "Heat source", "Camera style"],
        input_mode=InputMode.PREVIOUS_FINAL_FRAME,
        estimated_clip_duration_seconds=10,
        completion_range="35-80%",
        is_final_scene=False,
        reserved_future_actions=SCENE_2_RESERVED,
        forbidden_future_actions=SCENE_2_FORBIDDEN,
        exact_stop_state=SCENE_2_COOK_STOP,
    ),
    ScenePlan(
        scene_id=3,
        name="Finishing & Plating",
        start_state=SCENE_2_COOK_STOP,
        ordered_actions=COOKING_PLATING_ACTIONS,
        end_state=SCENE_3_FINAL_STOP,
        forbidden_changes=[
            "Kitchen",
            "Lighting",
            "Serveware",
            "Camera style",
            "Cooking state continuity",
        ],
        input_mode=InputMode.PREVIOUS_FINAL_FRAME,
        estimated_clip_duration_seconds=10,
        completion_range="80-100%",
        is_final_scene=True,
        reserved_future_actions=[],
        forbidden_future_actions=[],
        exact_stop_state=SCENE_3_FINAL_STOP,
    ),
]


COOKING_SELECTION_SCHEMA = {
    "type": "object",
    "title": "Miniature Cooking Options",
    "required": ["dish_key"],
    "properties": {
        "dish_key": {
            "type": "string",
            "title": "Dish",
            "enum": list(KOREAN_DISHES.keys()),
            "x-enum-labels": [dish["name"] for dish in KOREAN_DISHES.values()],
        },
    },
    "x-ui-order": ["dish_key"],
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
    first_frame_factory=lambda topic, dur, ctx: (
        {"first_frame_prompt": make_first_frame_prompt(ctx["dish_key"])}
        if ctx.get("scene_id") == 1
        else {}
    ),
    scene_prompt_factory=lambda topic, dur, ctx: {
        "video_prompt": make_scene_video_prompt(ctx["scene_id"], ctx["dish_key"])
    },
    audio_contract={
        "type": "asmr_only",
        "description": "Only satisfying ASMR sounds: knife chops, water drips, sizzle, boil, simmer, pour, drizzle, gentle clink. No voices, no music, no narration.",
    },
    negative_prompt_base=COOKING_NEGATIVE_BASE,
    template_exclusions=[
        "miniature people",
        "tiny chef",
        "voice",
        "music",
        "traditional kitchen tools (non-miniature)",
    ],
)

register_profile(cooking_profile)


def make_style_bible(dish_key: str) -> StyleBible:
    dish = KOREAN_DISHES[dish_key]
    return StyleBible(
        identity_lock=COOKING_IDENTITY_LOCK,
        materials={
            "primary": dish["ingredients"],
            "secondary": [dish["cookware"], dish["heat_source"], dish["serveware"]],
            "tools": [
                "miniature knife",
                "miniature ladle",
                "miniature spatula",
                "miniature chopsticks",
                "miniature tongs",
            ],
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
    return (
        f"Ultra-realistic 8K HDR macro cinematography, 100mm macro lens, extreme close-up, "
        f"soft focus pulls. Giant human hands only, no miniature people, raw ingredients for "
        f"{dish['name']} laid out on a natural wooden cutting board in a clean modern kitchen "
        f"with softly blurred background. No cutting or heat yet; the ingredients are still "
        f"unprepared and ready to begin the prep stage. Miniature knife, ladle, spatula, and "
        f"tea light candle remain visible but unused. Identical kitchen, lighting, cutting "
        f"board, and hand position carry into the next scene. One uninterrupted locked composition, cumulative ingredient state, "
        f"no alternate camera, no zoom or reframe during cooking, no completed-state jump, no ingredient-state loss. No voices, no music, only "
        f"satisfying ASMR sounds. Negative Prompt: {COOKING_NEGATIVE_BASE}."
    )


def _build_scene_prompt(scene_id: int, dish: dict) -> str:
    scene_plan = SCENE_PLANS_30S[scene_id - 1]
    if scene_id == 1:
        prompt = (
            f"Ultra-realistic 8K HDR macro cinematography, 100mm macro lens, extreme close-up, "
            f"soft focus pulls. Giant human hands only, no miniature people, {dish['name']} "
            f"prep stage on a natural wooden cutting board in a clean modern kitchen with a "
            f"miniature knife, ladle, spatula, and tea light candle visible but still unused. "
            f"Start from raw ingredients only and complete washing, sorting, slicing, cubing, "
            f"chopping, and mincing into miniature prep bowls. Exact input/start state: raw "
            f"ingredients only, before any heat or cookware is used. Exact stop state: {SCENE_1_PREP_STOP}. "
            f"Stop immediately at this exact state and do not advance beyond the current preparation stage. "
            f"Same kitchen, same lighting, same "
            f"camera, same hand choreography. {STATE_PERMANENCE_RULE}. {COOKING_CONTINUITY_LOCK}. No voices, no music, "
            f"only satisfying ASMR sounds. Negative Prompt: {COOKING_NEGATIVE_BASE}."
        )
    elif scene_id == 2:
        prompt = (
            f"Ultra-realistic 8K HDR macro cinematography, 100mm macro lens, extreme close-up, "
            f"seamless continuation from the previous exact stop state. Giant human hands only, "
            f"same kitchen, same cutting board, same lighting, same camera. Move the prepared "
            f"ingredients into {dish['cookware']} over {dish['heat_source']} and cook them with "
            f"realistic sizzling, bubbling, simmering, and browning until the dish is fully "
            f"cooked. Exact input/start state: {SCENE_1_PREP_STOP}. Exact stop state: {SCENE_2_COOK_STOP}. "
            f"Stop immediately at this exact state and do not advance beyond the current cooking stage. Same "
            f"kitchen, same lighting, same camera, same heat source, same ASMR-only soundscape. "
            f"{STATE_PERMANENCE_RULE}. {COOKING_CONTINUITY_LOCK}. "
            f"Negative Prompt: {COOKING_NEGATIVE_BASE}."
        )
    else:
        prompt = (
            f"Ultra-realistic 8K HDR macro cinematography, 100mm macro lens, extreme close-up, "
            f"seamless continuation from the previous exact stop state. Giant human hands only, "
            f"same kitchen, same cookware, same lighting, same camera. Ladle the fully cooked "
            f"{dish['name']} into {dish['serveware']}, drizzle the finishing oil, sprinkle the "
            f"garnish, and reveal the plated steam-filled hero shot. Exact input/start state: "
            f"{SCENE_2_COOK_STOP}. Exact stop state: {SCENE_3_FINAL_STOP}. "
            f"All earlier prep and cooking steps remain complete and unchanged. Same kitchen, same "
            f"lighting, same camera, same ASMR-only soundscape. {STATE_PERMANENCE_RULE}. {COOKING_CONTINUITY_LOCK}. "
            f"Negative Prompt: {COOKING_NEGATIVE_BASE}."
        )
    return append_scene_control_block(prompt, scene_plan, state_policy="cooking")


def make_scene_video_prompt(scene_id: int, dish_key: str) -> str:
    dish = KOREAN_DISHES[dish_key]
    return _build_scene_prompt(scene_id, dish)


def get_available_dishes() -> dict:
    return {k: v["name"] for k, v in KOREAN_DISHES.items()}
