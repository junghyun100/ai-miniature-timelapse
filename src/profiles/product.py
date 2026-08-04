"""
Product Assembly Profile (product.assembly)

Per Section 13.7:
- Workflow: SINGLE_CLIP_FROM_MASTER
- Duration: 10s single clip, 30s and 60s progressive assembly variants
- Subtypes: watch, camera, sneaker, robot, dinosaur, wizard_house, spaceship, hoverbike, mech, dragon
"""

from __future__ import annotations

from ..profile_types import (
    InputMode,
    Profile,
    ScenePlan,
    StyleBible,
    WorkflowMode,
    append_scene_control_block,
    register_profile,
)

# Subtype registry per Table 13.7
PRODUCT_SUBTYPES = {
    "watch": {
        "label": "Mechanical Watch",
        "materials": ["stainless steel", "sapphire crystal", "leather strap", "movement parts"],
        "key_parts": ["case", "bezel", "dial", "hands", "crown", "movement", "strap", "buckle"],
    },
    "camera": {
        "label": "Vintage Camera",
        "materials": ["metal body", "leatherette", "glass lens elements", "shutter mechanism"],
        "key_parts": ["body", "lens barrel", "shutter", "viewfinder", "film compartment", "winder"],
    },
    "sneaker": {
        "label": "Sneaker",
        "materials": ["mesh upper", "foam midsole", "rubber outsole", "laces", "overlays"],
        "key_parts": [
            "upper",
            "midsole",
            "outsole",
            "lacing system",
            "tongue",
            "heel counter",
            "insole",
        ],
    },
    "robot": {
        "label": "Robot",
        "materials": ["metal", "plastic", "wire", "LED", "servo", "circuit board"],
        "key_parts": ["head", "torso", "arms", "legs", "joints", "power core", "sensor array"],
    },
    "dinosaur": {
        "label": "Dinosaur Skeleton",
        "materials": ["fossil bone replica", "metal armature", "display base"],
        "key_parts": ["skull", "spine", "ribs", "pelvis", "femurs", "tail vertebrae", "claws"],
    },
    "wizard_house": {
        "label": "Wizard House",
        "materials": ["wood", "stone", "thatch", "crystal", "potion bottles", "magic effects"],
        "key_parts": [
            "base",
            "walls",
            "roof",
            "chimney",
            "door",
            "windows",
            "tower",
            "magical details",
        ],
    },
    "spaceship": {
        "label": "Spaceship",
        "materials": ["metal hull", "engine parts", "thrusters", "cockpit glass", "solar panels"],
        "key_parts": [
            "hull",
            "engines",
            "cockpit",
            "wings/fins",
            "landing gear",
            "antenna",
            "thrusters",
        ],
    },
    "hoverbike": {
        "label": "Hoverbike",
        "materials": ["metal frame", "anti-grav engines", "seat", "handlebars", "thrusters"],
        "key_parts": [
            "frame",
            "engines",
            "seat",
            "handlebars",
            "thrusters",
            "stabilizers",
            "dashboard",
        ],
    },
    "mech": {
        "label": "Mech",
        "materials": ["armor plates", "hydraulics", "actuators", "cockpit", "weapons", "joints"],
        "key_parts": [
            "torso",
            "legs",
            "arms",
            "cockpit",
            "shoulders",
            "hips",
            "feet",
            "hands",
            "weapons",
        ],
    },
    "dragon": {
        "label": "Dragon",
        "materials": ["scales", "wings", "claws", "horns", "eyes", "tail", "spikes"],
        "key_parts": [
            "head",
            "neck",
            "body",
            "wings",
            "front legs",
            "hind legs",
            "tail",
            "horns",
            "spikes",
        ],
    },
}


PRODUCT_SUBTYPE_STAGES = {
    "watch": [
        "Place the main plate into the open case base while keeping the movement bridge separate",
        "Seat the gear train and mainspring barrel, then place the movement bridge and lock its screws",
        "Align the dial and press the hour and minute hands into place",
        "Close the case with bezel, crystal, and crown fitted",
        "Thread the leather strap through the lugs and fasten the buckle",
        "Sweep away dust and reveal the finished mechanical watch",
    ],
    "camera": [
        "Lock the shutter box and body shell to the base frame",
        "Install the lens barrel and glass elements into the front mount",
        "Fit the film chamber, winding spool, and viewfinder assembly",
        "Close the top plate and back door, then add control dials",
        "Attach leatherette panels, strap lugs, and small branding details",
        "Brush away debris and reveal the finished vintage camera",
    ],
    "sneaker": [
        "Stretch the upper over the last and align the toe box",
        "Bond the foam midsole to the rubber outsole, then attach the sole unit to the lasted upper",
        "Pull the laces through the eyelets and settle the tongue",
        "Attach the heel counter and side overlays for structure",
        "Add stitching lines, logo marks, and texture touches",
        "Sweep away fibers and reveal the finished sneaker",
    ],
    "robot": [
        "Assemble the torso frame and power core housing",
        "Mount the arms, shoulder joints, and elbow actuators",
        "Attach the legs, hips, and knee joints",
        "Install the head, sensor array, and chest armor",
        "Add armor plates, wiring, and light details",
        "Brush away dust and reveal the finished robot",
    ],
    "dinosaur": [
        "Pin the skull and spine into the metal armature",
        "Attach ribs, pelvis, and tail vertebrae in sequence",
        "Add the front legs, hind legs, and claw joints",
        "Lock the existing neck and tail pose, then secure the assembled skeleton to the display base",
        "Add surface texture, color wash, and fossil detail",
        "Brush away crumbs and reveal the finished dinosaur skeleton",
    ],
    "wizard_house": [
        "Set the stone base and lower walls on the foundation",
        "Raise upper walls, door frame, and window openings",
        "Build the roof structure and chimney",
        "Attach tower pieces, balconies, and trims",
        "Add crystals, potion bottles, lanterns, and magical details",
        "Sweep away dust and reveal the finished wizard house",
    ],
    "spaceship": [
        "Assemble the fuselage shell and central hull frame",
        "Mount the engines, thrusters, and power conduits",
        "Fit the cockpit, canopy, and antenna array",
        "Attach wings, fins, landing gear, and exterior panels",
        "Add decals, panel lines, and energy details",
        "Brush away debris and reveal the finished spaceship",
    ],
    "hoverbike": [
        "Build the frame and anti-gravity engine core",
        "Mount the seat, handlebars, and dashboard housing",
        "Attach thrusters and stabilizers under the frame",
        "Fit the fairings, control lines, and body covers",
        "Add light strips, decals, and mechanical detailing",
        "Sweep away dust and reveal the finished hoverbike",
    ],
    "mech": [
        "Assemble the torso core and hip frame",
        "Mount the legs, feet, and hydraulic pistons",
        "Attach the arms, shoulders, and hand assemblies",
        "Install the head unit, cockpit, and joint covers",
        "Add armor plates, weapons, and wiring details",
        "Brush away debris and reveal the finished mech",
    ],
    "dragon": [
        "Shape the head and neck over the internal armature",
        "Attach body segments, wings, and shoulder joints",
        "Mount the front legs, hind legs, and claws",
        "Extend the tail, horns, and back spikes",
        "Add scale texture, paint wash, and eye details",
        "Brush away dust and reveal the finished dragon figure",
    ],
}

PRODUCT_IDENTITY_LOCK_BASE = (
    "hyper-realistic macro ASMR assembly timelapse, giant human hands only, "
    "no miniature people, no small people, no tiny workers, no human figures, no characters, "
    "precise mechanical/organic assembly logic, "
    "parts move from a visible edge staging tray through visible hand contact and attach in realistic order; installed parts remain fixed, "
    "camera angle, scale, workbench position, and lighting physically fixed throughout, "
    "tweezers, mini screwdriver, soft brush, 85mm lens, shallow depth of field, "
    "8K product quality, bright workshop lighting"
)

PRODUCT_FINAL_ONLY_LOCK = (
    "100% disassembled parts to fully assembled model, "
    "final brush sweep, final polish, final reveal, "
    "final step leaves only the fully assembled model on a clean workbench"
)


PRODUCT_NEGATIVE_BASE = (
    "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, "
    "bad anatomy, deformed hands, blurry, miniature people, tiny workers, "
    "floating parts, teleporting parts, completed model at start, messy final workbench"
)

PRODUCT_CONTINUITY_LOCK = (
    "one uninterrupted locked composition, cumulative installed state, "
    "no alternate camera, no zoom, no reframe during assembly, no completed-state jump, no installed-state loss, "
    "no morphing into a different product, no rebuild from scratch"
)


def _sanitize_reserved_future_action(action: str) -> str:
    lowered = action.lower()
    if any(
        token in lowered
        for token in ("final reveal", "final polish", "clean workbench", "final finish")
    ):
        return "later finishing stage"
    return action


def _sanitize_reserved_future_actions(actions: list[str]) -> list[str]:
    sanitized: list[str] = []
    for action in actions:
        cleaned_action = _sanitize_reserved_future_action(action)
        if cleaned_action not in sanitized:
            sanitized.append(cleaned_action)
    return sanitized


def _summarize_actions(actions: list[str]) -> str:
    return "; ".join(action for action in actions if action)


def _summarize_future_actions(actions: list[str]) -> str:
    return ", ".join(actions[:3]) if actions else "no remaining actions"


def _get_stage_actions(subtype: str) -> list[str]:
    if subtype not in PRODUCT_SUBTYPE_STAGES:
        raise KeyError(f"Unknown product subtype: {subtype}")
    return PRODUCT_SUBTYPE_STAGES[subtype]


def _scene_ranges_for_duration(duration_seconds: int) -> list[str]:
    if duration_seconds == 30:
        return ["0-30%", "30-75%", "75-100%"]
    if duration_seconds == 60:
        return ["0-15%", "15-35%", "35-55%", "55-75%", "75-90%", "90-100%"]
    return ["0-100%"]


def _scene_names_for_duration(duration_seconds: int) -> list[str]:
    if duration_seconds == 30:
        return ["Core Assembly", "Integration", "Detail Reveal"]
    if duration_seconds == 60:
        return [
            "Core Structure",
            "Major Sub-Assemblies",
            "Sub-assembly Integration",
            "External Components",
            "Fine Details",
            "Final Reveal",
        ]
    return ["Full Assembly"]


def _scene_action_groups(stage_actions: list[str], duration_seconds: int) -> list[list[str]]:
    if duration_seconds == 30:
        return [stage_actions[0:2], stage_actions[2:4], stage_actions[4:6]]
    if duration_seconds == 60:
        return [[stage_actions[i]] for i in range(len(stage_actions))]
    return [stage_actions]


def _assembly_micro_actions(actions: list[str], is_final: bool) -> list[str]:
    """Turn broad stages into observable motions without inventing future work."""
    if len(actions) >= 4:
        return actions
    if is_final:
        return [
            *actions,
            "Inspect the completed subject without changing installed components",
            "Use the soft brush to clear dust and loose scraps",
            "Move every unused tool and loose material out of frame by hand",
            "Withdraw the hands and hold the clean final hero frame",
        ][:6]
    if len(actions) == 2:
        return [
            "Select only the components required for the first listed operation",
            actions[0],
            "Seat and secure the first new connections with visible tool contact",
            "Select only the components required for the second listed operation",
            actions[1],
            "Seat, verify, and leave every newly attached component fixed",
        ]
    joined = actions[0] if actions else "complete the current assembly operation"
    return [
        "Select only the components required for this stage",
        "Lift those components from the visible edge staging tray with the appropriate tool",
        "Align them to their intended attachment surfaces without disturbing installed work",
        joined,
        "Seat, press, stitch, pin, or fasten each new connection as physically appropriate",
        "Withdraw the tool and verify the newly attached components remain fixed",
    ]


def _build_scene_plans(subtype: str, duration_seconds: int) -> list[ScenePlan]:
    stage_actions = _get_stage_actions(subtype)
    action_groups = _scene_action_groups(stage_actions, duration_seconds)
    ranges = _scene_ranges_for_duration(duration_seconds)
    names = _scene_names_for_duration(duration_seconds)
    plans: list[ScenePlan] = []

    for idx, actions in enumerate(action_groups):
        is_final = idx == len(action_groups) - 1
        future_actions = _sanitize_reserved_future_actions(
            [action for later in action_groups[idx + 1 :] for action in later]
        )
        completed_summary = _summarize_actions(actions) or PRODUCT_SUBTYPES[subtype]["label"]
        exact_stop_state = (
            f"Completed actions in this scene: {completed_summary}. "
            f"The {PRODUCT_SUBTYPES[subtype]['label'].lower()} remains visibly incomplete; all not-yet-used parts remain visible and untouched in the edge staging tray."
            f" Installed parts remain visible and fixed."
            if not is_final
            else (
                f"{PRODUCT_SUBTYPES[subtype]['label']} fully assembled alone on a clean workbench. "
                "Installed parts remain visible and fixed."
            )
        )
        plans.append(
            ScenePlan(
                scene_id=idx + 1,
                name=names[idx],
                start_state=(
                    "All parts disassembled on workbench"
                    if idx == 0
                    else plans[idx - 1].exact_stop_state
                ),
                ordered_actions=actions,
                end_state=exact_stop_state,
                forbidden_changes=[
                    "Camera angle",
                    "Lighting",
                    "Workbench surface",
                    "No floating parts",
                    "No teleporting parts",
                ],
                input_mode=InputMode.MASTER_IMAGE if idx == 0 else InputMode.PREVIOUS_FINAL_FRAME,
                estimated_clip_duration_seconds=10,
                completion_range=ranges[idx],
                is_final_scene=is_final,
                reserved_future_actions=future_actions,
                forbidden_future_actions=[] if is_final else future_actions,
                exact_stop_state=exact_stop_state,
                visible_micro_actions=_assembly_micro_actions(actions, is_final),
            )
        )

    return plans


DEFAULT_PRODUCT_SUBTYPE = "watch"


SCENE_PLAN_10S = _build_scene_plans(DEFAULT_PRODUCT_SUBTYPE, 10)
SCENE_PLANS_30S = _build_scene_plans(DEFAULT_PRODUCT_SUBTYPE, 30)
SCENE_PLANS_60S = _build_scene_plans(DEFAULT_PRODUCT_SUBTYPE, 60)


def _make_style_bible(subtype: str) -> StyleBible:
    st = PRODUCT_SUBTYPES[subtype]
    return StyleBible(
        identity_lock=PRODUCT_IDENTITY_LOCK_BASE,
        materials={
            "primary": st["materials"],
            "secondary": ["paint", "decals", "adhesive", "lubricant"],
            "tools": [
                "tweezers",
                "mini screwdriver",
                "soft brush",
                "nippers",
                "magnifying glass",
                "file",
            ],
        },
        camera={
            "lens": "85mm",
            "angle": "macro_closeup",
            "movement": "fixed",
            "distance": "macro",
        },
        lighting={
            "key": "bright workshop overhead",
            "fill": "soft bounce",
            "mood": "bright_clean",
            "consistency": "locked",
        },
        color_palette={
            "primary": ["model-specific"],
            "accent": ["chrome", "painted details", "metallic"],
            "background": "workbench surface",
            "tone": "cool_cinematic",
        },
        workspace={
            "surface": "wooden workbench",
            "environment": "bright workshop",
            "clutter_rule": "parts_disappear",
        },
        hands_rule="hands_with_tools",
        motion_rule="stop_motion_assembly",
        negative_prompt_base=PRODUCT_NEGATIVE_BASE,
    )


def _make_first_frame_prompt(subtype: str) -> str:
    st = PRODUCT_SUBTYPES[subtype]
    parts_list = ", ".join(st["key_parts"])
    return (
        f"Hyper-realistic macro photo of 100% disassembled miniature {st['label']} "
        f"model parts neatly arranged on a wooden workbench, giant human hands only, "
        f"no miniature people, no small people, no tiny workers, no human figures, "
        f"no characters, no completed model visible, {parts_list} separated clearly, "
        f"tweezers, mini screwdriver, soft brush, nippers, 85mm lens, shallow depth of field, "
        f"8K product photo quality, bright workshop lighting, {st['label']}, scene: Master Image."
    )


def _make_scene_video_prompt(subtype: str) -> str:
    st = PRODUCT_SUBTYPES[subtype]
    model_lower = st["label"].lower()
    "1. Core structure placed on workbench. 2. Major sub-assemblies built (engine, movement, frame). 3. Sub-assemblies joined to core. 4. External components attached (panels, covers, details). 5. Fine details added (decals, paint touches, small parts). 6. Final brush sweep — completed model alone on clean workbench. "
    return (
        f"hyper-realistic macro ASMR assembly timelapse, giant human hands only, "
        f"no miniature people, no small people, no tiny workers, no human figures, no characters, "
        f"precise assembly logic, 100% disassembled parts to fully assembled model, "
        f"no floating or teleporting parts, parts move by visible hand contact from the visible edge staging tray and attach in realistic order, "
        f"final step leaves only the fully assembled model on a clean "
        f"workbench, tweezers, mini screwdriver, soft brush, nippers, 85mm lens, shallow depth "
        f"of field, 8K product quality, bright workshop lighting, {model_lower}, scene: Assembly. "
        f"After explicit hand cleanup, unused loose parts are moved to the staging tray. "
        f"By the final step, the workspace is completely clean, leaving only the fully assembled model. "
        f"Negative Prompt: {PRODUCT_NEGATIVE_BASE}."
    )


PRODUCT_SELECTION_SCHEMA = {
    "type": "object",
    "title": "Product Assembly Options",
    "required": ["subtype"],
    "properties": {
        "subtype": {
            "type": "string",
            "title": "Product subtype",
            "enum": list(PRODUCT_SUBTYPES.keys()),
            "x-enum-labels": [subtype["label"] for subtype in PRODUCT_SUBTYPES.values()],
        },
    },
    "x-ui-order": ["subtype"],
}


def _select_scene_plan(duration_seconds: int, scene_id: int, subtype: str) -> ScenePlan:
    plans = _build_scene_plans(subtype, duration_seconds)
    if scene_id < 1 or scene_id > len(plans):
        raise ValueError(f"scene_id {scene_id} is out of range for duration {duration_seconds}")
    return plans[scene_id - 1]


def _build_prompt_prefix(subtype: str, scene_plan: ScenePlan, duration_seconds: int) -> str:
    label = PRODUCT_SUBTYPES[subtype]["label"]
    base = (
        f"hyper-realistic macro ASMR assembly timelapse, giant human hands only, "
        f"no miniature people, no small people, no tiny workers, no human figures, no characters, "
        f"precise mechanical assembly logic, no floating or teleporting parts, "
        f"tweezers, mini screwdriver, soft brush, nippers, 85mm lens, shallow depth of field, "
        f"8K product quality, bright workshop lighting, {label}, scene: {scene_plan.name}. "
    )
    continuity_lock = f"{PRODUCT_CONTINUITY_LOCK}. "

    if scene_plan.is_final_scene or duration_seconds == 10:
        return (
            base
            + continuity_lock
            + f"{PRODUCT_IDENTITY_LOCK_BASE}. "
            + f"{PRODUCT_FINAL_ONLY_LOCK}. "
            + "After explicit hand cleanup, unused loose parts are moved to the staging tray. "
            + "By the final step, the workspace is completely clean, leaving only the fully assembled model. "
        )

    return (
        base
        + continuity_lock
        + f"{PRODUCT_IDENTITY_LOCK_BASE}. "
        + "The subject remains visibly incomplete in this scene. "
    )


product_profile = Profile(
    profile_id="product.assembly",
    version="2.0.0",
    topic_label="Product Assembly",
    workflow_mode=WorkflowMode.SINGLE_CLIP_FROM_MASTER,
    allowed_total_durations=[10, 30, 60],
    default_total_duration=10,
    clip_duration_seconds=10,
    scene_plans=SCENE_PLAN_10S,
    scene_plans_factory=lambda topic, dur, ctx: _build_scene_plans(ctx["subtype"], dur),
    selection_schema=PRODUCT_SELECTION_SCHEMA,
    style_bible_factory=lambda topic, dur, ctx: make_style_bible(ctx["subtype"]),
    first_frame_factory=lambda topic, dur, ctx: (
        {"first_frame_prompt": make_first_frame_prompt(ctx["subtype"])}
        if ctx.get("scene_id") == 1
        else {}
    ),
    scene_prompt_factory=lambda topic, dur, ctx: {
        "video_prompt": make_scene_video_prompt(
            ctx["scene_id"], ctx["subtype"], dur, ctx.get("scene_plan")
        )
    },
    audio_contract={
        "type": "asmr_only",
        "description": "Assembly sounds: clicks, snaps, screw turns, brush sweeps. No voices, no music.",
    },
    negative_prompt_base=PRODUCT_NEGATIVE_BASE,
    template_exclusions=[
        "completed model at start",
        "floating parts",
        "teleporting parts",
        "messy final workbench",
    ],
    workflow_mode_by_duration={
        10: WorkflowMode.SINGLE_CLIP_FROM_MASTER,
        30: WorkflowMode.REFERENCE_FRAME_RELAY,
        60: WorkflowMode.REFERENCE_FRAME_RELAY,
    },
)

register_profile(product_profile)


def make_style_bible(subtype: str) -> StyleBible:
    return _make_style_bible(subtype)


def make_first_frame_prompt(subtype: str) -> str:
    return _make_first_frame_prompt(subtype)


def make_scene_video_prompt(
    scene_id: int,
    subtype: str,
    duration_seconds: int | None = None,
    scene_plan: ScenePlan | None = None,
) -> str:
    if scene_plan is None:
        resolved_duration = duration_seconds if duration_seconds is not None else 10
        scene_plan = _select_scene_plan(resolved_duration, scene_id, subtype)
        duration_seconds = resolved_duration
    else:
        duration_seconds = duration_seconds if duration_seconds is not None else 10

    prompt = _build_prompt_prefix(subtype, scene_plan, duration_seconds)
    return append_scene_control_block(
        prompt + f"Negative Prompt: {PRODUCT_NEGATIVE_BASE}.",
        scene_plan,
        state_policy="assembly",
    )
