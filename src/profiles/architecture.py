"""
Korean Architecture Profile (architecture.korean)

Per Section 13.5:
- Workflow: REFERENCE_FRAME_RELAY
- Durations: 30s (3 scenes), 60s (6 scenes)
- Subtypes: hanok, palace, temple, seowon, modern_hanok, dolmen
- Identity: Korean traditional wooden architecture, hanok, tiled roof, wooden beams, stone foundation
"""

from ..profile_types import (
    Profile, ScenePlan, WorkflowMode, StyleBible, InputMode, register_profile
)


# Subtype registry per Table 13.5
ARCHITECTURE_SUBTYPES = {
    "hanok": {
        "label": "Hanok (Traditional Korean House)",
        "materials": ["wood", "clay tiles (giwa)", "stone foundation", "hanji paper windows", "ondol floor stones"],
        "key_features": ["curved tiled roof (cheoma)", "exposed wooden beams (daeryang)", "courtyard (madang)", "ondol heating"],
    },
    "palace": {
        "label": "Palace Architecture (Gung)",
        "materials": ["painted wood (dancheong)", "glazed tiles (yonggiwa)", "stone platforms (gidan)", "metal ornaments"],
        "key_features": ["multi-tiered roof", "bracket systems (gongpo)", "raised stone platform", "ornate dancheong patterns"],
    },
    "temple": {
        "label": "Buddhist Temple (Sa)",
        "materials": ["natural wood", "gray roof tiles", "stone lanterns", "paper screens", "bronze bells"],
        "key_features": ["main hall (daeungjeon)", "pagoda (tap)", "bell pavilion (jongru)", "meditative courtyard"],
    },
    "seowon": {
        "label": "Seowon (Confucian Academy)",
        "materials": ["unpainted wood", "clay tiles", "white plaster walls", "wooden floors", "stone foundations"],
        "key_features": ["lecture hall (myeongnyundang)", "shrine (sadang)", "dormitories (jaesa)", "serene garden with pond"],
    },
    "modern_hanok": {
        "label": "Modern Hanok",
        "materials": ["engineered wood", "modern glazing", "concrete foundation", "traditional tiles", "hanji-inspired screens"],
        "key_features": ["open floor plan", "floor-to-ceiling windows", "minimalist interior", "courtyard integration"],
    },
    "dolmen": {
        "label": "Dolmen / Megalithic",
        "materials": ["massive capstone", "supporting stones", "earth mound", "weathered stone", "burial goods"],
        "key_features": ["table-type dolmen (northern)", "go-table type (southern)", "burial chamber", "prehistoric monument"],
    },
}


ARCH_IDENTITY_LOCK = (
    "macro cinematography, 100mm lens, extreme close-up, soft focus pulls, "
    "Korean traditional wooden architecture, hanok, tiled roof, wooden beams, stone foundation"
)


ARCH_NEGATIVE_BASE = "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry."


# 30s plan (3 scenes × 10s)
SCENE_PLANS_30S = [
    ScenePlan(
        scene_id=1,
        name="Foundation & Framework",
        start_state="Empty workbench with materials",
        ordered_actions=[
            "Lay foundation stones with mortar",
            "Place base timbers (sill plates) on stone foundation",
            "Erect vertical posts, mortise-and-tenon joints fitted with wooden mallet",
            "Secure horizontal beams (girders) onto posts",
        ],
        end_state="Complete timber framework standing on stone foundation",
        forbidden_changes=[
            "Workbench", "Lighting", "Camera angle", "Tool positions"
        ],
        input_mode=InputMode.MASTER_IMAGE,
        estimated_clip_duration_seconds=10,
    ),
    ScenePlan(
        scene_id=2,
        name="Roof Structure",
        start_state="Framework ready for roof",
        ordered_actions=[
            "Lift and position rafters onto beam framework, precise angle cuts visible",
            "Place ridge beam, rafters secured with traditional joinery",
            "Add purlins horizontally, creating roof grid",
            "Lay clay tiles from bottom edge upward, overlapping perfectly",
        ],
        end_state="Complete tiled roof with curved eaves, ridge ornaments in place",
        forbidden_changes=["Workbench", "Lighting", "Camera angle", "Established framework"],
        input_mode=InputMode.PREVIOUS_FINAL_FRAME,
        estimated_clip_duration_seconds=10,
    ),
    ScenePlan(
        scene_id=3,
        name="Walls, Details & Completion",
        start_state="Roof complete, walls open",
        ordered_actions=[
            "Fit wall panels (wattle-and-daub or wooden) between posts",
            "Install hanji paper windows in lattice frames",
            "Paint dancheong patterns on exposed beams and eaves",
            "Place stone steps and courtyard stones",
        ],
        end_state="Fully assembled hanok with tiled roof, paper windows, painted details, stone courtyard",
        forbidden_changes=["Roof structure", "Workbench", "Lighting", "Camera angle"],
        input_mode=InputMode.PREVIOUS_FINAL_FRAME,
        estimated_clip_duration_seconds=10,
    ),
]


# 60s plan (6 scenes × 10s)
SCENE_PLANS_60S = [
    ScenePlan(1, "Foundation & Framework", "Empty workbench with materials",
        ["Lay foundation stones", "Place base timbers", "Erect vertical posts", "Secure horizontal beams"],
        "Complete timber framework on stone foundation",
        InputMode.MASTER_IMAGE, 10),
    ScenePlan(2, "Roof Structure", "Framework ready for roof",
        ["Position rafters", "Place ridge beam", "Add purlins", "Lay clay tiles"],
        "Complete tiled roof with curved eaves",
        InputMode.PREVIOUS_FINAL_FRAME, 10),
    ScenePlan(3, "Walls & Windows", "Roof complete, walls open",
        ["Fit wall panels", "Install hanji window frames", "Apply paper to lattices", "Add decorative trim"],
        "Enclosed structure with paper windows",
        InputMode.PREVIOUS_FINAL_FRAME, 10),
    ScenePlan(4, "Interior & Furnishings", "Structure enclosed",
        ["Lay ondol floor channels", "Place floor stones", "Arrange low furniture", "Add scholarly objects"],
        "Furnished interior visible through open doors",
        InputMode.PREVIOUS_FINAL_FRAME, 10),
    ScenePlan(5, "Garden & Landscape", "Interior complete",
        ["Plant moss and ground cover", "Position stone lantern", "Lay stepping stones", "Plant miniature pine"],
        "Building integrated into garden setting",
        InputMode.PREVIOUS_FINAL_FRAME, 10),
    ScenePlan(6, "Atmosphere & Hero Shot", "Garden complete",
        ["Morning light shifts across courtyard", "Gentle steam from ondol floor", "Camera pulls to hero angle", "Focus on curved roof silhouette"],
        "Cinematic hero shot, serene atmosphere",
        InputMode.PREVIOUS_FINAL_FRAME, 10),
]


ARCH_SELECTION_SCHEMA = {
    "type": "object",
    "required": ["subtype", "duration_seconds"],
    "properties": {
        "subtype": {"type": "string", "enum": list(ARCHITECTURE_SUBTYPES.keys())},
        "duration_seconds": {"type": "integer", "enum": [30, 60]},
    },
}


architecture_profile = Profile(
    profile_id="architecture.korean",
    version="2.0.0",
    topic_label="Korean Architecture",
    workflow_mode=WorkflowMode.REFERENCE_FRAME_RELAY,
    allowed_total_durations=[30, 60],
    default_total_duration=30,
    clip_duration_seconds=10,
    scene_plans=SCENE_PLANS_30S,
    scene_plans_factory=lambda topic, dur, ctx: SCENE_PLANS_60S if dur == 60 else SCENE_PLANS_30S,
    selection_schema=ARCH_SELECTION_SCHEMA,
    style_bible_factory=lambda topic, dur, ctx: make_style_bible(ctx["subtype"]),
    first_frame_factory=lambda topic, dur, ctx: {"first_frame_prompt": make_first_frame_prompt(ctx["subtype"])} if ctx.get("scene_id") == 1 else {},
    scene_prompt_factory=lambda topic, dur, ctx: {"video_prompt": make_scene_video_prompt(ctx["scene_id"], ctx["subtype"])},
    audio_contract={
        "type": "asmr_only",
        "description": "Wood joinery, stone setting, brush strokes, paper rustling. No voices, no music."
    },
    negative_prompt_base=ARCH_NEGATIVE_BASE,
    template_exclusions=["modern", "steel", "concrete", "glass", "neon", "electricity"],
)

register_profile(architecture_profile)


def get_scene_plans(duration_seconds: int) -> list[ScenePlan]:
    return SCENE_PLANS_60S if duration_seconds == 60 else SCENE_PLANS_30S


def make_style_bible(subtype: str) -> StyleBible:
    st = ARCHITECTURE_SUBTYPES[subtype]
    return StyleBible(
        identity_lock=ARCH_IDENTITY_LOCK,
        materials={
            "primary": st["materials"],
            "secondary": ["moss", "lichen", "seasonal foliage"],
            "tools": ["miniature chisel", "tiny trowel", "brush", "magnifying glass", "wooden mallet"],
        },
        camera={
            "lens": "100mm macro",
            "angle": "extreme_closeup",
            "movement": "soft_focus_pull",
            "distance": "extreme_macro",
        },
        lighting={
            "key": "soft directional morning light",
            "fill": "ambient skylight",
            "mood": "warm_cinematic",
            "consistency": "locked",
        },
        color_palette={
            "primary": ["warm wood tones", "terracotta", "stone gray"],
            "accent": ["dancheong red/green/blue", "gold leaf"],
            "background": "soft blurred nature",
            "tone": "warm_natural",
        },
        workspace={
            "surface": "dark wooden workbench",
            "environment": "traditional carpentry workshop",
            "clutter_rule": "organized_chaos",
        },
        hands_rule="giant_hands_only",
        motion_rule="stop_motion_assembly",
        negative_prompt_base=ARCH_NEGATIVE_BASE,
    )


def make_first_frame_prompt(subtype: str) -> str:
    st = ARCHITECTURE_SUBTYPES[subtype]
    return (
        "Ultra realistic macro photography, miniature construction site, sand or soil surface, "
        "giant human fingers interacting with miniature materials, tiny realistic construction tools, "
        "partially prepared foundation area, 8K detail, cinematic studio lighting, shallow depth of field. "
        f"Building type: {st['label']}."
    )


def make_scene_video_prompt(scene_id: int, subtype: str) -> str:
    st = ARCHITECTURE_SUBTYPES[subtype]

    # Reference prompt global rules (exact from reference)
    global_rules = (
        "ultra fast timelapse speed, human hands continuously constructing and moving rapidly, "
        "multiple rapid scene cuts, cinematic macro photography, "
        "miniature people forbidden, only giant human hands appear. "
    )

    # Scene descriptions matching reference exactly
    if scene_id == 1:
        # 30s: Foundation & Walls / 60s: Foundation
        if "dolmen" in subtype.lower():
            scene_desc = (
                "Giant hands survey empty site, measure and mark foundation layout on compacted earth. "
                "Hands place massive capstone support stones with precision. "
                "Mortar applied, foundation stones set level and aligned."
            )
        else:
            scene_desc = (
                "Giant hands measure and mark foundation layout on compacted earth. "
                "Miniature cement mixed and spread for foundation. "
                "Foundation bricks/stones laid precisely with mortar. "
                "Wall frames and window/door frames constructed up from foundation."
            )
    elif scene_id == 2:
        # 30s: Roofing & Exterior / 60s: Roof Structure
        if "dolmen" in subtype.lower():
            scene_desc = (
                "Hands position remaining support stones, checking stability. "
                "Massive capstone lifted and placed atop supports with perfect alignment. "
                "Earth mound built around structure, burial chamber sealed."
            )
        else:
            scene_desc = (
                "Roof framework assembled: rafters positioned, ridge beam placed. "
                "Clay tiles/panels installed from bottom edge upward, overlapping perfectly. "
                "Exterior walls finished, doors and windows installed with decorative trim."
            )
    elif scene_id == 3:
        # 30s: Painting & Landscaping Reveal / 60s: Walls & Windows
        if "dolmen" in subtype.lower():
            scene_desc = (
                "Weathering effects applied to stone surfaces. "
                "Surrounding landscape arranged with period-appropriate vegetation. "
                "Camera pulls back to reveal complete megalithic monument."
            )
        else:
            scene_desc = (
                "Wall panels fitted between structural posts. "
                "Hanji paper windows installed in lattice frames. "
                "Exterior decorative details added to eaves and trim."
            )
    elif scene_id == 4:
        # 60s: Interior & Furnishings
        scene_desc = (
            "Ondol floor heating channels laid beneath stone slabs. "
            "Low furniture placed: table, cushions, storage chest. "
            "Scholarly objects arranged: incense burner, brush holder. "
            "Paper screens slid into door frames."
        )
    elif scene_id == 5:
        # 60s: Garden & Landscape
        scene_desc = (
            "Moss and ground cover planted around foundation. "
            "Stone lantern positioned in courtyard. "
            "Stepping stones laid along garden path. "
            "Miniature pine tree planted near corner."
        )
    elif scene_id == 6:
        # 60s: Atmosphere & Hero Shot
        scene_desc = (
            "Soft morning light shifts, casting long shadows across courtyard. "
            "Gentle steam rises from ondol-heated floor visible through door gap. "
            "Camera pulls back to reveal full composition. "
            "Final focus pull to hero angle: curved roof silhouette against sky. "
            "Normal cinematic speed for final reveal."
        )
    else:
        scene_desc = "Construction continues with precision."

    negative = f"Negative Prompt: {ARCH_NEGATIVE_BASE}."

    return global_rules + scene_desc + " " + negative