"""
Product Assembly Profile (product.assembly)

Per Section 13.7:
- Workflow: SINGLE_CLIP_FROM_MASTER
- Duration: 10s (single clip)
- Subtypes: watch, camera, sneaker, robot, dinosaur, wizard_house, spaceship, hoverbike, mech, dragon
"""

from ..profile_types import (
    Profile, ScenePlan, WorkflowMode, StyleBible, InputMode, register_profile
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
        "key_parts": ["upper", "midsole", "outsole", "lacing system", "tongue", "heel counter", "insole"],
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
        "key_parts": ["base", "walls", "roof", "chimney", "door", "windows", "tower", "magical details"],
    },
    "spaceship": {
        "label": "Spaceship",
        "materials": ["metal hull", "engine parts", "thrusters", "cockpit glass", "solar panels"],
        "key_parts": ["hull", "engines", "cockpit", "wings/fins", "landing gear", "antenna", "thrusters"],
    },
    "hoverbike": {
        "label": "Hoverbike",
        "materials": ["metal frame", "anti-grav engines", "seat", "handlebars", "thrusters"],
        "key_parts": ["frame", "engines", "seat", "handlebars", "thrusters", "stabilizers", "dashboard"],
    },
    "mech": {
        "label": "Mech",
        "materials": ["armor plates", "hydraulics", "actuators", "cockpit", "weapons", "joints"],
        "key_parts": ["torso", "legs", "arms", "cockpit", "shoulders", "hips", "feet", "hands", "weapons"],
    },
    "dragon": {
        "label": "Dragon",
        "materials": ["scales", "wings", "claws", "horns", "eyes", "tail", "spikes"],
        "key_parts": ["head", "neck", "body", "wings", "front legs", "hind legs", "tail", "horns", "spikes"],
    },
}


PRODUCT_ASSEMBLY_STEPS = [
    "Core structure placed on workbench",
    "Major sub-assemblies built (engine, movement, frame)",
    "Sub-assemblies joined to core",
    "External components attached (panels, covers, details)",
    "Fine details added (decals, paint touches, small parts)",
    "Final brush sweep — completed model alone on clean workbench",
]


PRODUCT_IDENTITY_LOCK = (
    "hyper-realistic macro ASMR assembly timelapse, giant human hands only, "
    "no miniature people, precise mechanical/organic assembly logic, "
    "100% disassembled parts to fully assembled model, "
    "parts attach in realistic order and disappear from workbench as installed, "
    "final step leaves only the fully assembled model on a clean workbench, "
    "tweezers, mini screwdriver, soft brush, 85mm lens, shallow depth of field, "
    "8K product quality, bright workshop lighting"
)


PRODUCT_NEGATIVE_BASE = (
    "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, "
    "bad anatomy, deformed hands, blurry, miniature people, tiny workers, "
    "floating parts, teleporting parts, completed model at start, messy final workbench"
)


def _make_style_bible(subtype: str) -> StyleBible:
    st = PRODUCT_SUBTYPES[subtype]
    return StyleBible(
        identity_lock=PRODUCT_IDENTITY_LOCK,
        materials={
            "primary": st["materials"],
            "secondary": ["paint", "decals", "adhesive", "lubricant"],
            "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "magnifying glass", "file"],
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
    steps_str = " ".join([
        "1. Core structure placed on workbench. "
        "2. Major sub-assemblies built (engine, movement, frame). "
        "3. Sub-assemblies joined to core. "
        "4. External components attached (panels, covers, details). "
        "5. Fine details added (decals, paint touches, small parts). "
        "6. Final brush sweep — completed model alone on clean workbench. "
    ])
    return (
        f"hyper-realistic macro ASMR assembly timelapse, giant human hands only, "
        f"no miniature people, no small people, no tiny workers, no human figures, no characters, "
        f"precise assembly logic, 100% disassembled parts to fully assembled model, "
        f"no floating or teleporting parts, parts attach in realistic order and disappear from "
        f"workbench as installed, final step leaves only the fully assembled model on a clean "
        f"workbench, tweezers, mini screwdriver, soft brush, nippers, 85mm lens, shallow depth "
        f"of field, 8K product quality, bright workshop lighting, {model_lower}, scene: Assembly. "
        f"As parts are attached, they logically disappear from the workbench. "
        f"By the final step, the workspace is completely clean, leaving only the fully assembled model. "
        f"Negative Prompt: {PRODUCT_NEGATIVE_BASE}."
    )


# Single scene (10s)
SCENE_PLAN = [
    ScenePlan(
        scene_id=1,
        name="Assembly",
        start_state="All parts disassembled on workbench",
        ordered_actions=PRODUCT_ASSEMBLY_STEPS,
        end_state="Fully assembled model alone on clean workbench",
        forbidden_changes=[
            "Camera angle", "Lighting", "Workbench surface", "Tool positions",
            "Parts must not float/teleport", "Completed model cannot appear before final step"
        ],
        input_mode=InputMode.MASTER_IMAGE,
        estimated_clip_duration_seconds=10,
    ),
]


PRODUCT_SELECTION_SCHEMA = {
    "type": "object",
    "required": ["subtype"],
    "properties": {
        "subtype": {"type": "string", "enum": list(PRODUCT_SUBTYPES.keys())},
    },
}


product_profile = Profile(
    profile_id="product.assembly",
    version="2.0.0",
    topic_label="Product Assembly",
    workflow_mode=WorkflowMode.SINGLE_CLIP_FROM_MASTER,
    allowed_total_durations=[10],
    default_total_duration=10,
    clip_duration_seconds=10,
    scene_plans=SCENE_PLAN,
    selection_schema=PRODUCT_SELECTION_SCHEMA,
    style_bible_factory={},
    first_frame_factory={},
    scene_prompt_factory={},
    audio_contract={
        "type": "asmr_only",
        "description": "Assembly sounds: clicks, snaps, screw turns, brush sweeps. No voices, no music."
    },
    negative_prompt_base=PRODUCT_NEGATIVE_BASE,
    template_exclusions=["completed model at start", "floating parts", "teleporting parts", "messy final workbench"],
)

register_profile(product_profile)


def make_style_bible(subtype: str) -> StyleBible:
    return _make_style_bible(subtype)


def make_first_frame_prompt(subtype: str) -> str:
    return _make_first_frame_prompt(subtype)


def make_scene_video_prompt(subtype: str) -> str:
    return _make_scene_video_prompt(subtype)