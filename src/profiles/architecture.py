"""
Architecture Profile (architecture.korean).

Per Section 13.5:
- Workflow: REFERENCE_FRAME_RELAY
- Durations: 30s (3 scenes), 60s (6 scenes)
- Profile id kept as architecture.korean for storage compatibility
- Subtypes now cover the original 6 Korean architectures plus 7 broader
  architecture types used by the UI
"""

from __future__ import annotations

from typing import cast

from ..profile_types import (
    InputMode,
    Profile,
    ScenePlan,
    StyleBible,
    WorkflowMode,
    append_scene_control_block,
    register_profile,
)

ARCHITECTURE_SUBTYPES = {
    "hanok": {
        "label": "Hanok (Traditional Korean House)",
        "family": "traditional_korean",
        "materials": [
            "wood",
            "clay tiles (giwa)",
            "stone foundation",
            "hanji paper windows",
            "ondol floor stones",
        ],
        "key_features": [
            "curved tiled roof (cheoma)",
            "exposed wooden beams (daeryang)",
            "courtyard (madang)",
            "ondol heating",
        ],
        "color_palette": {
            "primary": ["warm cedar brown", "stone gray", "aged clay black"],
            "accent": ["hanji ivory", "muted vermilion", "soft moss green"],
            "background": "earth-toned courtyard soil",
            "tone": "warm_traditional",
        },
    },
    "palace": {
        "label": "Palace Architecture (Gung)",
        "family": "traditional_korean",
        "materials": [
            "painted wood (dancheong)",
            "glazed tiles (yonggiwa)",
            "stone platforms (gidan)",
            "metal ornaments",
        ],
        "key_features": [
            "multi-tiered roof",
            "bracket systems (gongpo)",
            "raised stone platform",
            "ornate dancheong patterns",
        ],
        "color_palette": {
            "primary": ["royal vermilion", "jade green", "deep indigo"],
            "accent": ["gold leaf", "ink black", "warm ivory"],
            "background": "muted palace courtyard soil",
            "tone": "regal_traditional",
        },
    },
    "temple": {
        "label": "Buddhist Temple (Sa)",
        "family": "traditional_korean",
        "materials": [
            "natural wood",
            "gray roof tiles",
            "stone lanterns",
            "paper screens",
            "bronze bells",
        ],
        "key_features": [
            "main hall (daeungjeon)",
            "pagoda (tap)",
            "bell pavilion (jongru)",
            "meditative courtyard",
        ],
        "color_palette": {
            "primary": ["weathered cedar", "charcoal gray", "stone moss"],
            "accent": ["saffron", "quiet gold", "pine green"],
            "background": "soft mountain earth",
            "tone": "serene_traditional",
        },
    },
    "seowon": {
        "label": "Seowon (Confucian Academy)",
        "family": "traditional_korean",
        "materials": [
            "unpainted wood",
            "clay tiles",
            "white plaster walls",
            "wooden floors",
            "stone foundations",
        ],
        "key_features": [
            "lecture hall (myeongnyundang)",
            "shrine (sadang)",
            "dormitories (jaesa)",
            "serene garden with pond",
        ],
        "color_palette": {
            "primary": ["pine wood", "plaster white", "slate gray"],
            "accent": ["bamboo green", "ink brown", "pond blue"],
            "background": "soft garden soil",
            "tone": "calm_traditional",
        },
    },
    "modern_hanok": {
        "label": "Modern Hanok",
        "family": "hybrid_traditional",
        "materials": [
            "engineered wood",
            "modern glazing",
            "stone foundation",
            "traditional roof tiles",
            "hanji-inspired screens",
        ],
        "key_features": [
            "open floor plan",
            "floor-to-ceiling windows",
            "minimalist interior",
            "courtyard integration",
        ],
        "color_palette": {
            "primary": ["warm oak", "matte black", "soft stone gray"],
            "accent": ["hanji cream", "smoke blue", "subtle terracotta"],
            "background": "clean courtyard gravel",
            "tone": "modern_traditional",
        },
    },
    "dolmen": {
        "label": "Dolmen / Megalithic",
        "family": "megalithic",
        "materials": [
            "massive capstone",
            "supporting stones",
            "earth mound",
            "weathered stone",
            "burial goods",
        ],
        "key_features": [
            "table-type dolmen (northern)",
            "go-table type (southern)",
            "burial chamber",
            "prehistoric monument",
        ],
        "color_palette": {
            "primary": ["granite gray", "earth brown", "moss green"],
            "accent": ["weathered slate", "dry lichen", "soil beige"],
            "background": "bare archaeological soil",
            "tone": "ancient_earthy",
        },
    },
    "villa": {
        "label": "Villa",
        "family": "residential",
        "materials": [
            "stucco walls",
            "oak window frames",
            "ceramic roof tiles",
            "glass balcony doors",
            "garden terrace stone",
        ],
        "key_features": [
            "luxury low-rise silhouette",
            "balcony railings",
            "garden-facing windows",
            "terrace and pergola details",
        ],
        "color_palette": {
            "primary": ["warm ivory", "sand beige", "oak brown"],
            "accent": ["terracotta", "soft olive", "bronze"],
            "background": "sunlit garden soil",
            "tone": "elegant_residential",
        },
    },
    "store": {
        "label": "Store",
        "family": "commercial",
        "materials": [
            "plaster facade",
            "glass storefront panels",
            "metal awning",
            "signage frame",
            "display window shelves",
        ],
        "key_features": [
            "street-facing storefront",
            "wide entry glazing",
            "sign band",
            "compact retail footprint",
        ],
        "color_palette": {
            "primary": ["off white", "charcoal", "clear glass blue"],
            "accent": ["sign red", "brass", "warm gray"],
            "background": "urban sidewalk tone",
            "tone": "clean_commercial",
        },
    },
    "school": {
        "label": "School",
        "family": "civic",
        "materials": [
            "brick walls",
            "painted concrete",
            "large classroom windows",
            "metal railings",
            "entry canopy",
        ],
        "key_features": [
            "repeating classroom bays",
            "flagpole or entry marker",
            "corridor window rhythm",
            "playground-facing frontage",
        ],
        "color_palette": {
            "primary": ["light brick", "pale blue", "warm gray"],
            "accent": ["playground green", "navy", "white trim"],
            "background": "schoolyard sand",
            "tone": "bright_civic",
        },
    },
    "hotel": {
        "label": "Hotel",
        "family": "hospitality",
        "materials": [
            "stone cladding",
            "glass curtain walls",
            "brass trim",
            "lobby canopy",
            "balcony modules",
        ],
        "key_features": [
            "grand entrance",
            "stacked guest-room floors",
            "balcony rhythm",
            "refined facade lighting",
        ],
        "color_palette": {
            "primary": ["stone beige", "deep navy", "smoke glass"],
            "accent": ["brass gold", "warm taupe", "soft charcoal"],
            "background": "luxury plaza surface",
            "tone": "refined_hospitality",
        },
    },
    "apartment": {
        "label": "Apartment",
        "family": "residential",
        "materials": [
            "reinforced concrete frame",
            "balcony railings",
            "modular windows",
            "shared podium cladding",
            "entry lobby glazing",
        ],
        "key_features": [
            "repeating floor stack",
            "modular facade rhythm",
            "balcony grid",
            "shared residential core",
        ],
        "color_palette": {
            "primary": ["white", "concrete gray", "graphite"],
            "accent": ["warm wood", "cool silver", "light blue"],
            "background": "clean urban site dirt",
            "tone": "modern_residential",
        },
    },
    "factory": {
        "label": "Factory",
        "family": "industrial",
        "materials": [
            "steel trusses",
            "corrugated metal siding",
            "concrete pads",
            "loading bay doors",
            "ventilation stacks",
        ],
        "key_features": [
            "high-bay industrial volume",
            "wide service openings",
            "roof ventilation lines",
            "functional loading zone",
        ],
        "color_palette": {
            "primary": ["steel gray", "concrete taupe", "industrial blue"],
            "accent": ["safety orange", "rust brown", "warning yellow"],
            "background": "gritty factory yard soil",
            "tone": "industrial_cool",
        },
    },
    "barn": {
        "label": "Barn",
        "family": "agricultural",
        "materials": [
            "timber frame",
            "vertical planks",
            "red siding",
            "metal roof panels",
            "hay loft doors",
        ],
        "key_features": [
            "gabled barn silhouette",
            "loft opening",
            "large sliding doors",
            "farmyard presence",
        ],
        "color_palette": {
            "primary": ["barn red", "weathered wood brown", "straw gold"],
            "accent": ["galvanized silver", "cream trim", "sage green"],
            "background": "farm soil and straw",
            "tone": "rustic_agricultural",
        },
    },
}


ARCHITECTURE_SUBTYPE_ORDER = list(ARCHITECTURE_SUBTYPES.keys())


def _palette_phrase(subtype: str) -> str:
    palette = ARCHITECTURE_SUBTYPES[subtype]["color_palette"]
    return ", ".join(
        [
            *(palette.get("primary", []) or []),
            *(palette.get("accent", []) or []),
        ]
    )


def _materials_phrase(subtype: str) -> str:
    materials = ARCHITECTURE_SUBTYPES[subtype]["materials"]
    return ", ".join(materials)


def _features_phrase(subtype: str) -> str:
    features = ARCHITECTURE_SUBTYPES[subtype]["key_features"]
    return ", ".join(features)


def _identity_lock(subtype: str) -> str:
    data = ARCHITECTURE_SUBTYPES[subtype]
    materials = ", ".join(cast(list[str], data["materials"])[:4])
    features = ", ".join(cast(list[str], data["key_features"])[:3])
    palette = _palette_phrase(subtype)
    return (
        "macro cinematography, 100mm lens, extreme close-up, soft focus pulls, "
        f"Architecture subtype: {data['label']}, {materials}, {features}, recommended palette: {palette}"
    )


ARCH_NEGATIVE_BASE = (
    "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, "
    "bad anatomy, deformed hands, blurry, miniature people, tiny workers, small people, "
    "human figures"
)


ARCHITECTURE_INITIAL_STATE = (
    "Completely unstarted site: bare sand or soil, with all subtype materials organized in a visible edge staging tray, "
    "no foundation, no walls, no posts, no roof structure, no finish work, "
    "no later-stage elements already visible."
)


def _scene_plan(
    scene_id: int,
    name: str,
    start_state: str,
    ordered_actions: list[str],
    end_state: str,
    completion_range: str,
    exact_stop_state: str,
    reserved_future_actions: list[str],
    forbidden_future_actions: list[str],
    is_final_scene: bool,
) -> ScenePlan:
    return ScenePlan(
        scene_id=scene_id,
        name=name,
        start_state=start_state,
        ordered_actions=ordered_actions,
        end_state=end_state,
        forbidden_changes=[
            "Do not change identity, camera, lighting, or scale.",
            "Do not advance into later construction stages early.",
        ],
        input_mode=InputMode.MASTER_IMAGE if scene_id == 1 else InputMode.PREVIOUS_FINAL_FRAME,
        estimated_clip_duration_seconds=10,
        completion_range=completion_range,
        is_final_scene=is_final_scene,
        reserved_future_actions=reserved_future_actions,
        forbidden_future_actions=forbidden_future_actions,
        exact_stop_state=exact_stop_state,
    )


def _build_scene_plans_30s() -> list[ScenePlan]:
    scene1 = _scene_plan(
        scene_id=1,
        name="Foundation & Walls",
        start_state=ARCHITECTURE_INITIAL_STATE,
        ordered_actions=[
            "Survey and mark the footprint on the bare ground.",
            "Spread miniature cement and place the foundation stones or slab.",
            "Raise the structural posts or frame and build the wall sections.",
            "Build and align only the rough door and window opening frames; leave finished doors, glazing, and trim separate.",
        ],
        end_state="Foundation, walls, and rough door and window opening frames installed, with finished units, roof, and finish materials visible and untouched in the edge staging tray.",
        completion_range="0-35%",
        exact_stop_state="Foundation, walls, and rough door and window opening frames installed, with finished units, roof, and finish materials visible and untouched in the edge staging tray.",
        reserved_future_actions=[
            "Assemble the roof frame and install roof tiles or panels.",
            "Complete the exterior surfaces, doors, windows, and decorative details.",
            "Apply primer, paint, weathering, landscaping, and the reveal.",
        ],
        forbidden_future_actions=[
            "Do not begin roofing or exterior finishing yet.",
            "Do not apply primer, paint, weathering, or landscaping yet.",
        ],
        is_final_scene=False,
    )

    scene2 = _scene_plan(
        scene_id=2,
        name="Roofing & Exterior",
        start_state=scene1.exact_stop_state,
        ordered_actions=[
            "Assemble the rafters, ridge, and subtype-specific roof frame.",
            "Install the roof tiles, panels, or metal covering in logical rows.",
            "Apply finish layers over the completed wall structure without rebuilding it, then fit finished doors, glazing, and window units into the existing rough openings.",
            "Attach subtype-specific trim and decorative details while paint and landscaping materials remain separate.",
        ],
        end_state="Roofing and exterior details installed, with primer, paint, weathering, and landscaping materials visible and untouched in the edge staging tray.",
        completion_range="35-75%",
        exact_stop_state="Roofing and exterior details installed, with primer, paint, weathering, and landscaping materials visible and untouched in the edge staging tray.",
        reserved_future_actions=[
            "Apply primer, paint, and weathering.",
            "Add landscaping and perform the reveal.",
        ],
        forbidden_future_actions=[
            "Do not begin painting or weathering yet.",
            "Do not add landscaping or perform the reveal yet.",
        ],
        is_final_scene=False,
    )

    scene3 = _scene_plan(
        scene_id=3,
        name="Painting & Landscaping Reveal",
        start_state=scene2.exact_stop_state,
        ordered_actions=[
            "Apply primer, subtype-appropriate paint, and weathering effects.",
            "Add grass, soil, fences, site details, or subtype-specific landscaping pieces.",
            "Remove the giant hands after the last landscaping placement.",
            "Perform the final cinematic reveal after the build is complete.",
        ],
        end_state="Completed architecture scene with painting, weathering, landscaping, and final reveal complete.",
        completion_range="75-100%",
        exact_stop_state="Completed architecture scene with painting, weathering, landscaping, and final reveal complete.",
        reserved_future_actions=[],
        forbidden_future_actions=[],
        is_final_scene=True,
    )

    return [scene1, scene2, scene3]


def _build_scene_plans_60s() -> list[ScenePlan]:
    scene1 = _scene_plan(
        scene_id=1,
        name="Foundation",
        start_state=ARCHITECTURE_INITIAL_STATE,
        ordered_actions=[
            "Survey and mark the footprint on the bare ground.",
            "Spread miniature cement across the prepared footprint.",
            "Place and level the foundation stones, slab, or pads.",
            "Keep wall, roof, and finish materials separated beside the work area.",
        ],
        end_state="Foundation laid and level, with wall, roof, and finish materials visible and untouched in the edge staging tray.",
        completion_range="0-15%",
        exact_stop_state="Foundation laid and level, with wall, roof, and finish materials visible and untouched in the edge staging tray.",
        reserved_future_actions=[
            "Build walls and install door and window frames.",
            "Assemble and cover the roof.",
            "Complete exterior, painting, weathering, landscaping, and reveal work.",
        ],
        forbidden_future_actions=[
            "Do not begin walls, roofing, exterior finishing, painting, or landscaping yet.",
        ],
        is_final_scene=False,
    )

    scene2 = _scene_plan(
        scene_id=2,
        name="Walls & Rough Openings",
        start_state=scene1.exact_stop_state,
        ordered_actions=[
            "Raise the structural posts, columns, or frame members.",
            "Build the subtype-specific wall sections in logical order.",
            "Build and align only the rough door and window opening frames; leave finished doors, glazing, and trim separate.",
            "Keep rafters, roof covering, and finish materials separated beside the work area.",
        ],
        end_state="Walls and rough door and window opening frames installed, with finished units, roofing, and finish materials visible and untouched in the edge staging tray.",
        completion_range="15-35%",
        exact_stop_state="Walls and rough door and window opening frames installed, with finished units, roofing, and finish materials visible and untouched in the edge staging tray.",
        reserved_future_actions=[
            "Assemble the roof frame and install roof tiles or panels.",
            "Complete exterior surfaces, doors, windows, and decorative details.",
            "Apply painting, weathering, landscaping, and reveal work.",
        ],
        forbidden_future_actions=[
            "Do not begin roofing, exterior finishing, painting, or landscaping yet.",
        ],
        is_final_scene=False,
    )

    scene3 = _scene_plan(
        scene_id=3,
        name="Roofing",
        start_state=scene2.exact_stop_state,
        ordered_actions=[
            "Assemble the rafters, ridge, and subtype-specific roof frame.",
            "Lock the roof frame onto the wall structure.",
            "Install roof tiles, panels, or metal covering in logical rows.",
            "Keep exterior fixtures, paint, and landscaping materials separated.",
        ],
        end_state="Roof frame and roof covering installed, with exterior fixtures, paint, and landscaping materials visible and untouched in the edge staging tray.",
        completion_range="35-55%",
        exact_stop_state="Roof frame and roof covering installed, with exterior fixtures, paint, and landscaping materials visible and untouched in the edge staging tray.",
        reserved_future_actions=[
            "Complete exterior surfaces, doors, windows, and decorative details.",
            "Apply primer, paint, and weathering.",
            "Add landscaping and perform the reveal.",
        ],
        forbidden_future_actions=[
            "Do not begin exterior finishing, painting, or landscaping yet.",
        ],
        is_final_scene=False,
    )

    scene4 = _scene_plan(
        scene_id=4,
        name="Exterior",
        start_state=scene3.exact_stop_state,
        ordered_actions=[
            "Apply cladding, plaster, or finish layers over the completed walls without rebuilding their structure.",
            "Fit finished door leaves, window units or glazing, and railings into the existing rough openings.",
            "Attach trim, brackets, ornaments, signage, or other subtype-specific details.",
            "Keep primer, paint, weathering, and landscaping materials separated.",
        ],
        end_state="Exterior surfaces, doors, windows, and decorative details installed, with painting and landscaping materials visible and untouched in the edge staging tray.",
        completion_range="55-75%",
        exact_stop_state="Exterior surfaces, doors, windows, and decorative details installed, with painting and landscaping materials visible and untouched in the edge staging tray.",
        reserved_future_actions=[
            "Apply primer, paint, and weathering.",
            "Add landscaping and perform the reveal.",
        ],
        forbidden_future_actions=[
            "Do not begin painting, weathering, landscaping, or the reveal yet.",
        ],
        is_final_scene=False,
    )

    scene5 = _scene_plan(
        scene_id=5,
        name="Painting",
        start_state=scene4.exact_stop_state,
        ordered_actions=[
            "Apply primer to the appropriate exterior surfaces.",
            "Paint only the installed surfaces and trim in the subtype-specific palette; add no new structural or decorative parts.",
            "Add controlled weathering and age variation.",
            "Keep grass, soil, fences, and other landscaping materials separated.",
        ],
        end_state="Primer, paint, and weathering applied, with all landscaping materials visible and untouched in the edge staging tray.",
        completion_range="75-90%",
        exact_stop_state="Primer, paint, and weathering applied, with all landscaping materials visible and untouched in the edge staging tray.",
        reserved_future_actions=[
            "Add grass, soil, fences, and subtype-specific landscaping.",
            "Remove the hands and perform the cinematic reveal.",
        ],
        forbidden_future_actions=[
            "Do not begin landscaping or the reveal yet.",
        ],
        is_final_scene=False,
    )

    scene6 = _scene_plan(
        scene_id=6,
        name="Landscaping & Reveal",
        start_state=scene5.exact_stop_state,
        ordered_actions=[
            "Add grass, topsoil, fences, landscape stones, and surface paving outside the completed building footprint.",
            "Remove the giant hands from the frame after the last placement.",
            "Perform the normal cinematic speed zoom-out reveal.",
            "Hold the final hero view of the architecture subtype.",
        ],
        end_state="Completed architecture scene with landscaping integrated and final reveal complete.",
        completion_range="90-100%",
        exact_stop_state="Completed architecture scene with landscaping integrated and final reveal complete.",
        reserved_future_actions=[],
        forbidden_future_actions=[],
        is_final_scene=True,
    )

    return [scene1, scene2, scene3, scene4, scene5, scene6]


SCENE_PLANS_30S = _build_scene_plans_30s()
SCENE_PLANS_60S = _build_scene_plans_60s()


def get_scene_plans(duration_seconds: int) -> list[ScenePlan]:
    return SCENE_PLANS_60S if duration_seconds == 60 else SCENE_PLANS_30S


def make_style_bible(subtype: str) -> StyleBible:
    st = ARCHITECTURE_SUBTYPES[subtype]
    return StyleBible(
        identity_lock=_identity_lock(subtype),
        materials={
            "primary": st["materials"],
            "secondary": ["moss", "lichen", "seasonal foliage"],
            "tools": [
                "miniature chisel",
                "tiny trowel",
                "brush",
                "magnifying glass",
                "wooden mallet",
            ],
            "subtype_focus": st["key_features"],
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
        color_palette=st["color_palette"],
        workspace={
            "surface": "dark wooden workbench",
            "environment": "architectural miniature workshop",
            "clutter_rule": "organized_chaos",
        },
        hands_rule="giant_hands_only",
        motion_rule="stop_motion_assembly",
        negative_prompt_base=ARCH_NEGATIVE_BASE,
    )


def make_first_frame_prompt(subtype: str) -> str:
    st = ARCHITECTURE_SUBTYPES[subtype]
    materials = _materials_phrase(subtype)
    features = _features_phrase(subtype)
    palette = _palette_phrase(subtype)
    return (
        "Ultra realistic macro photography, miniature construction site, sand or soil surface, "
        "giant human fingers interacting with miniature materials, tiny realistic construction tools, "
        f"exact starting state: {ARCHITECTURE_INITIAL_STATE} "
        "One giant hand hovers above the first foundation piece without touching it; nothing has been built yet. "
        "Later-stage walls, roof, and finish details remain visible and untouched in the edge staging tray. "
        "8K detail, cinematic studio lighting, shallow depth of field. "
        f"Architecture subtype: {st['label']}. "
        f"Primary subtype materials: {materials}. "
        f"Subtype features: {features}. "
        f"Recommended palette: {palette}."
    )


def _resolve_scene_plan(
    scene_id: int,
    duration_seconds: int | None,
    scene_plan: ScenePlan | None,
) -> ScenePlan:
    if scene_plan is not None:
        return scene_plan

    if duration_seconds == 60:
        return SCENE_PLANS_60S[scene_id - 1]
    if duration_seconds == 30:
        return SCENE_PLANS_30S[scene_id - 1]

    if scene_id <= 3:
        return SCENE_PLANS_30S[scene_id - 1]
    return SCENE_PLANS_60S[scene_id - 1]


def _negative_prompt_suffix() -> str:
    return f"Negative Prompt: {ARCH_NEGATIVE_BASE}"


def _scene_direction(subtype: str, plan: ScenePlan) -> str:
    st = ARCHITECTURE_SUBTYPES[subtype]
    materials = _materials_phrase(subtype)
    features = _features_phrase(subtype)
    palette = _palette_phrase(subtype)
    return (
        f"Architecture subtype: {st['label']}. "
        f"Subtype materials: {materials}. "
        f"Subtype features: {features}. "
        f"Recommended palette: {palette}. "
        f"Scene focus: {plan.name}. "
    )


def make_scene_video_prompt(
    scene_id: int,
    subtype: str,
    duration_seconds: int | None = None,
    scene_plan: ScenePlan | None = None,
) -> str:
    plan = _resolve_scene_plan(scene_id, duration_seconds, scene_plan)

    global_rules = (
        "ultra fast timelapse speed, human hands continuously constructing and moving rapidly, "
        "rapid procedural timelapse in one uninterrupted locked camera composition, no editorial cuts or alternate shots, cinematic macro photography, giant human hands only, "
        "no miniature people, fixed identity, fixed camera, fixed lighting. "
    )
    if plan.is_final_scene:
        body = (
            "Final-only work may include landscaping, hands removed from frame, normal cinematic speed, "
            "and a cinematic zoom-out reveal. "
        )
    else:
        body = ""

    prompt = (f"{global_rules}{_scene_direction(subtype, plan)}{body}").rstrip()
    return append_scene_control_block(
        f"{prompt} {_negative_prompt_suffix()}", plan, state_policy="architecture"
    )


architecture_profile = Profile(
    profile_id="architecture.korean",
    version="2.0.0",
    topic_label="Architecture",
    workflow_mode=WorkflowMode.REFERENCE_FRAME_RELAY,
    allowed_total_durations=[30, 60],
    default_total_duration=30,
    clip_duration_seconds=10,
    scene_plans=SCENE_PLANS_30S,
    scene_plans_factory=lambda topic, dur, ctx: get_scene_plans(dur),
    selection_schema={
        "type": "object",
        "title": "Architecture Options",
        "required": ["subtype"],
        "properties": {
            "subtype": {
                "type": "string",
                "title": "Architecture subtype",
                "enum": ARCHITECTURE_SUBTYPE_ORDER,
                "x-enum-labels": [
                    ARCHITECTURE_SUBTYPES[subtype]["label"]
                    for subtype in ARCHITECTURE_SUBTYPE_ORDER
                ],
            }
        },
        "x-ui-order": ["subtype"],
    },
    style_bible_factory=lambda topic, dur, ctx: make_style_bible(ctx["subtype"]),
    first_frame_factory=lambda topic, dur, ctx: (
        {"first_frame_prompt": make_first_frame_prompt(ctx["subtype"])}
        if ctx.get("scene_id") == 1
        else {}
    ),
    scene_prompt_factory=lambda topic, dur, ctx: {
        "video_prompt": make_scene_video_prompt(
            ctx["scene_id"],
            ctx["subtype"],
            duration_seconds=dur,
            scene_plan=ctx.get("scene_plan"),
        )
    },
    audio_contract={
        "type": "asmr_only",
        "description": "Wood joinery, stone setting, brush strokes, paper rustling, metal fitting. No voices, no music.",
    },
    negative_prompt_base=ARCH_NEGATIVE_BASE,
    template_exclusions=[],
)


register_profile(architecture_profile)
