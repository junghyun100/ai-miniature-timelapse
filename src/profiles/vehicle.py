"""
Vehicle Assembly Profile — 10 Categories (car, motorcycle, airplane, boat, agricultural, helicopter, construction, spaceship, tank, bicycle)

Reference prompt based implementation per vehicle_assembly_reference.md
Each category has specific identity_lock, style_bible, scene_prompts, and assembly steps.
"""

from enum import Enum
from typing import Any, Optional, Callable

from ..profile_types import Profile, ScenePlan, WorkflowMode, InputMode, StyleBible, register_profile


class VehicleCategory(str, Enum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"
    AIRPLANE = "airplane"
    BOAT = "boat"
    AGRICULTURAL = "agricultural"
    HELICOPTER = "helicopter"
    CONSTRUCTION = "construction"
    SPACESHIP = "spaceship"
    TANK = "tank"
    BICYCLE = "bicycle"


VehicleSubtype = VehicleCategory  # Alias for backward compatibility


# Representative models per category (for UI suggestions)
VEHICLE_MODELS: dict[VehicleCategory, list[str]] = {
    VehicleCategory.CAR: ["Porsche 911", "Ford Mustang", "Toyota 2000GT", "Ferrari 250 GTO", "Mini Cooper", "Volkswagen Beetle", "BMW 3.0 CSL", "Nissan Skyline GT-R", "Chevrolet Corvette", "Jaguar E-Type"],
    VehicleCategory.MOTORCYCLE: ["Honda CB750", "Ducati 916", "Harley-Davidson Knucklehead", "Kawasaki Ninja ZX-10R", "BMW R nineT", "Triumph Bonneville", "Yamaha R1", "Moto Guzzi V7", "Indian Chief", "Royal Enfield Interceptor"],
    VehicleCategory.AIRPLANE: ["Boeing 707", "Supermarine Spitfire", "P-51 Mustang", "F-16 Fighting Falcon", "Cessna 172", "SR-71 Blackbird", "Concorde", "F-22 Raptor", "Mitsubishi Zero", "B-17 Flying Fortress"],
    VehicleCategory.BOAT: ["Chris-Craft Runabout", "America's Cup Yacht", "PT Boat", "U-Boat", "Titanic", "Viking Longship", "Sailing Frigate", "Speedboat", "Submarine", "Hovercraft"],
    VehicleCategory.AGRICULTURAL: ["John Deere 4020", "Ford 8N", "Case IH Magnum", "Fendt 1050", "Massey Ferguson 135", "New Holland T8", "Claas Xerion", "Deutz-Fahr 9340", "Valtra S374", "Kubota M7"],
    VehicleCategory.HELICOPTER: ["Bell 47", "UH-1 Huey", "AH-64 Apache", "Mi-24 Hind", "CH-47 Chinook", "Sikorsky S-76", "Robinson R44", "Eurocopter EC135", "Kamov Ka-50", "Boeing CH-47"],
    VehicleCategory.CONSTRUCTION: ["Caterpillar D11", "Komatsu PC8000", "Liebherr R9800", "Hitachi EX8000", "Volvo EC950", "JCB 3CX", "Case 580", "Doosan DX225", "Hyundai R210", "Sumitomo SH350"],
    VehicleCategory.SPACESHIP: ["Saturn V", "Falcon 9", "Space Shuttle", "Starship", "Soyuz", "Delta IV", "Ariane 5", "Atlas V", "Electron", "New Glenn"],
    VehicleCategory.TANK: ["M1 Abrams", "T-90", "Leopard 2", "Challenger 2", "Type 99", "K2 Black Panther", "Merkava Mk 4", "T-14 Armata", "Panther", "Tiger I"],
    VehicleCategory.BICYCLE: ["Pinarello Dogma", "Specialized S-Works", "Colnago C64", "Bianchi Oltre", "Cervélo R5", "Trek Madone", "Cannondale SuperSix", "Wilier Filante", "Factor Ostro", "Look 795"],
}

# Identity Lock per category
VEHICLE_IDENTITY_LOCKS: dict[VehicleCategory, str] = {
    VehicleCategory.CAR: "One coherent miniature car with unchanged wheelbase, body silhouette, paint color, glass shape, and component layout throughout.",
    VehicleCategory.MOTORCYCLE: "One coherent miniature motorcycle with unchanged frame geometry, engine position, wheelbase, handlebar shape, and component layout throughout.",
    VehicleCategory.AIRPLANE: "One coherent miniature airplane with unchanged fuselage length, wingspan, engine configuration, tail design, and landing gear layout throughout.",
    VehicleCategory.BOAT: "One coherent miniature boat with unchanged hull shape, deck layout, superstructure, propulsion type, and component arrangement throughout.",
    VehicleCategory.AGRICULTURAL: "One coherent miniature tractor with unchanged chassis dimensions, engine position, wheel/track configuration, cab shape, and implement mounting points throughout.",
    VehicleCategory.HELICOPTER: "One coherent miniature helicopter with unchanged fuselage shape, rotor configuration, tail boom length, engine position, and landing gear type throughout.",
    VehicleCategory.CONSTRUCTION: "One coherent miniature construction vehicle with unchanged track/wheel configuration, chassis dimensions, hydraulic system layout, boom/arm geometry, and cab position throughout.",
    VehicleCategory.SPACESHIP: "One coherent miniature spaceship with unchanged stage configuration, engine cluster arrangement, payload fairing shape, fin/grid fin layout, and overall silhouette throughout.",
    VehicleCategory.TANK: "One coherent miniature tank with unchanged hull shape, turret geometry, gun barrel length, track type, road wheel arrangement, and component layout throughout.",
    VehicleCategory.BICYCLE: "One coherent miniature bicycle with unchanged frame geometry, wheel size, drivetrain layout, handlebar type, saddle position, and component arrangement throughout.",
}

# Key parts per category for Master Image prompt
VEHICLE_KEY_PARTS: dict[VehicleCategory, str] = {
    VehicleCategory.CAR: "chassis, engine block, transmission, suspension, wheels, body panels, steering, interior components",
    VehicleCategory.MOTORCYCLE: "engine, frame, wheels, fork, swingarm, tank, exhaust, handlebars, controls",
    VehicleCategory.AIRPLANE: "fuselage, wings, engine/propeller, landing gear, tail, cockpit, control surfaces",
    VehicleCategory.BOAT: "hull, deck, mast/superstructure, engine, propeller, rudder, anchor, rigging",
    VehicleCategory.AGRICULTURAL: "engine, transmission, chassis, wheels/tracks, PTO, hydraulics, cab, drawbar",
    VehicleCategory.HELICOPTER: "main rotor, tail rotor, engine, transmission, fuselage, landing skids, cockpit, swashplate",
    VehicleCategory.CONSTRUCTION: "tracks/wheels, chassis, engine, hydraulic system, boom/arm, bucket, cab, counterweight",
    VehicleCategory.SPACESHIP: "stages, engines, fuel tanks, payload fairing, guidance, heat shield, landing legs, grid fins",
    VehicleCategory.TANK: "hull, turret, gun, tracks, engine, transmission, suspension, road wheels, optics",
    VehicleCategory.BICYCLE: "frame, fork, wheels, drivetrain, handlebars, saddle, brakes, chain, cranks",
}

# Assembly steps per category (6 steps matching reference)
VEHICLE_ASSEMBLY_STEPS: dict[VehicleCategory, list[str]] = {
    VehicleCategory.CAR: [
        "Engine block placed into chassis with precision",
        "Fasteners tightened securing powertrain",
        "Wheels and suspension mounted",
        "Steering rack installed and connected",
        "Body panels fitted seamlessly",
        "Final polish revealing complete model on clean workbench"
    ],
    VehicleCategory.MOTORCYCLE: [
        "Engine lowered into frame cradle",
        "Bolts torqued securing engine to frame",
        "Wheels and suspension fitted",
        "Fork and handlebars assembled",
        "Tank, seat, and bodywork mounted",
        "Final polish revealing complete bike on clean workbench"
    ],
    VehicleCategory.AIRPLANE: [
        "Engine mounted to fuselage/wing",
        "Fasteners securing powerplant and mounts",
        "Landing gear retracted and locked",
        "Control surfaces connected and tested",
        "Wings and tail surfaces fitted",
        "Final polish revealing complete aircraft on clean workbench"
    ],
    VehicleCategory.BOAT: [
        "Engine installed in hull",
        "Mounts and fasteners secured",
        "Propeller shaft and rudder connected",
        "Steering and controls linked",
        "Deck, superstructure, and rigging fitted",
        "Final polish revealing complete vessel on clean workbench"
    ],
    VehicleCategory.AGRICULTURAL: [
        "Engine mounted to chassis",
        "Transmission and PTO bolted in place",
        "Wheels/tracks and suspension fitted",
        "Hydraulics and cab installed",
        "Drawbar and implement mounts attached",
        "Final polish revealing complete tractor on clean workbench"
    ],
    VehicleCategory.HELICOPTER: [
        "Main transmission and engine installed",
        "Mast and rotor head secured",
        "Tail boom and tail rotor fitted",
        "Landing skids and controls connected",
        "Fuselage panels and cockpit glazed",
        "Final polish revealing complete helicopter on clean workbench"
    ],
    VehicleCategory.CONSTRUCTION: [
        "Engine and hydraulic pump installed",
        "Tracks/wheels and final drives fitted",
        "Boom and arm structure assembled",
        "Bucket and hydraulic cylinders connected",
        "Cab and counterweight mounted",
        "Final polish revealing complete machine on clean workbench"
    ],
    VehicleCategory.SPACESHIP: [
        "Engines mounted to first stage",
        "Stage separation mechanisms secured",
        "Fuel tanks and plumbing installed",
        "Guidance and avionics integrated",
        "Payload fairing and grid fins fitted",
        "Final polish revealing complete rocket on clean workbench"
    ],
    VehicleCategory.TANK: [
        "Engine and transmission installed in hull",
        "Suspension and road wheels fitted",
        "Tracks connected and tensioned",
        "Turret ring and turret mounted",
        "Gun, optics, and armor fitted",
        "Final polish revealing complete tank on clean workbench"
    ],
    VehicleCategory.BICYCLE: [
        "Bottom bracket and cranks installed",
        "Drivetrain (chain, cassette, derailleurs) fitted",
        "Wheels trued and mounted",
        "Handlebars, stem, and controls assembled",
        "Saddle, seatpost, and brakes installed",
        "Final polish revealing complete bicycle on clean workbench"
    ],
}

# Style Bible per category
VEHICLE_STYLE_BIBLES: dict[VehicleCategory, dict[str, Any]] = {
    VehicleCategory.CAR: {
        "materials": {"primary": ["die-cast metal", "plastic", "rubber tires", "clear plastic glass"], "secondary": ["paint", "chrome", "decals"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "file", "cement"]},
        "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
        "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
        "color_palette": {"primary": ["metallic silver", "gunmetal", "chrome"], "accent": ["model-specific paint"], "background": "clean workbench surface", "tone": "cool_cinematic"},
        "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.MOTORCYCLE: {
        "materials": {"primary": ["die-cast metal", "plastic", "rubber tires", "chrome"], "secondary": ["paint", "decals", "leather seat"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "torque wrench"]},
        "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
        "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
        "color_palette": {"primary": ["metallic silver", "chrome", "black"], "accent": ["model-specific paint"], "background": "clean workbench surface", "tone": "cool_cinematic"},
        "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.AIRPLANE: {
        "materials": {"primary": ["die-cast metal", "plastic", "rubber tires"], "secondary": ["paint", "decals", "panel lines"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "pin vise"]},
        "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
        "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
        "color_palette": {"primary": ["metallic silver", "aluminum", "olive drab"], "accent": ["model-specific markings"], "background": "clean workbench surface", "tone": "cool_cinematic"},
        "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.BOAT: {
        "materials": {"primary": ["die-cast metal", "plastic", "wood", "fabric sails"], "secondary": ["paint", "varnish", "rigging"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "needle"]},
        "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
        "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
        "color_palette": {"primary": ["white", "navy", "wood tones"], "accent": ["brass", "copper"], "background": "clean workbench surface", "tone": "cool_cinematic"},
        "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.AGRICULTURAL: {
        "materials": {"primary": ["die-cast metal", "plastic", "rubber tires/tracks"], "secondary": ["paint", "decals", "hydraulic hoses"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "wrench"]},
        "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
        "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
        "color_palette": {"primary": ["green", "red", "yellow", "blue"], "accent": ["chrome", "black"], "background": "clean workbench surface", "tone": "cool_cinematic"},
        "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.HELICOPTER: {
        "materials": {"primary": ["die-cast metal", "plastic", "composite rotor blades"], "secondary": ["paint", "decals", "clear canopy"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "pin vise"]},
        "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
        "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
        "color_palette": {"primary": ["olive drab", "gray", "camouflage"], "accent": ["red cross", "warning stripes"], "background": "clean workbench surface", "tone": "cool_cinematic"},
        "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.CONSTRUCTION: {
        "materials": {"primary": ["die-cast metal", "plastic", "rubber tracks/tires"], "secondary": ["paint", "decals", "hydraulic hoses"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "wrench", "allen keys"]},
        "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
        "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
        "color_palette": {"primary": ["yellow", "orange", "gray"], "accent": ["black tracks", "chrome"], "background": "clean workbench surface", "tone": "cool_cinematic"},
        "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.SPACESHIP: {
        "materials": {"primary": ["die-cast metal", "plastic", "composite"], "secondary": ["paint", "thermal tiles", "decals"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "torque wrench"]},
        "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
        "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
        "color_palette": {"primary": ["white", "black", "metallic"], "accent": ["engine glow", "grid fins"], "background": "clean workbench surface", "tone": "cool_cinematic"},
        "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.TANK: {
        "materials": {"primary": ["die-cast metal", "plastic", "rubber/metal tracks"], "secondary": ["paint", "decals", "photo-etched parts"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "file", "cement"]},
        "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
        "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
        "color_palette": {"primary": ["olive drab", "sand", "gray", "camouflage"], "accent": ["gun metal", "glass"], "background": "clean workbench surface", "tone": "cool_cinematic"},
        "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.BICYCLE: {
        "materials": {"primary": ["carbon fiber", "aluminum", "steel", "rubber tires"], "secondary": ["paint", "decals", "bar tape"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "chain tool", "allen keys"]},
        "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
        "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
        "color_palette": {"primary": ["carbon black", "metallic team colors"], "accent": ["chrome", "anodized"], "background": "clean workbench surface", "tone": "cool_cinematic"},
        "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
}

# Immutable negative prompt (fixed per spec — matches reference prompt exactly)
VEHICLE_NEGATIVE_BASE = "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry."

# Scene plans for 30s (3 scenes) and 60s (6 scenes)
def build_scene_plans_30s(category: VehicleCategory) -> list[ScenePlan]:
    """3 scenes for 30s total (3 x 10s)"""
    steps = VEHICLE_ASSEMBLY_STEPS[category]
    return [
        ScenePlan(
            scene_id=1,
            name="Foundation & Powertrain",
            start_state="all parts disassembled on workbench",
            ordered_actions=steps[:2],
            end_state="powertrain foundation complete",
            forbidden_changes=["Workbench", "Lighting", "Camera angle", "Chassis position"],
            input_mode=InputMode.MASTER_IMAGE,
        ),
        ScenePlan(
            scene_id=2,
            name="Running Gear & Structure",
            start_state="Scene 1 final frame",
            ordered_actions=steps[2:4],
            end_state="rolling chassis/structure complete",
            forbidden_changes=["Workbench", "Lighting", "Camera angle", "Chassis position", "Powertrain"],
            input_mode=InputMode.PREVIOUS_FINAL_FRAME,
        ),
        ScenePlan(
            scene_id=3,
            name="Body & Final Reveal",
            start_state="Scene 2 final frame",
            ordered_actions=steps[4:],
            end_state="complete model revealed",
            forbidden_changes=["Workbench", "Lighting", "Camera angle", "Chassis position", "Running gear"],
            input_mode=InputMode.PREVIOUS_FINAL_FRAME,
        ),
    ]


def build_scene_plans_60s(category: VehicleCategory) -> list[ScenePlan]:
    """6 scenes for 60s total (6 x 10s)"""
    steps = VEHICLE_ASSEMBLY_STEPS[category]
    return [
        ScenePlan(
            scene_id=1,
            name="Frame & Engine Mounts",
            start_state="all parts disassembled on workbench",
            ordered_actions=[steps[0], "engine mounts secured"],
            end_state="frame with engine mounts ready",
            forbidden_changes=InputMode.MASTER_IMAGE,
            input_mode=InputMode.MASTER_IMAGE,
        ),
        ScenePlan(
            scene_id=2,
            name="Powertrain Installation",
            start_state="Scene 1 final frame",
            ordered_actions=[steps[1], "transmission/driveshaft connected"],
            end_state="powertrain fully installed",
            forbidden_changes=["Workbench", "Lighting", "Camera angle", "Chassis position"],
            input_mode=InputMode.PREVIOUS_FINAL_FRAME,
        ),
        ScenePlan(
            scene_id=3,
            name="Running Gear",
            start_state="Scene 2 final frame",
            ordered_actions=[steps[2], steps[3] if len(steps) > 3 else "suspension/steering completed"],
            end_state="rolling chassis complete",
            forbidden_changes=["Workbench", "Lighting", "Camera angle", "Chassis position", "Powertrain"],
            input_mode=InputMode.PREVIOUS_FINAL_FRAME,
        ),
        ScenePlan(
            scene_id=4,
            name="Superstructure/Body",
            start_state="Scene 3 final frame",
            ordered_actions=[steps[min(4, len(steps)-1)], "main body/structure fitted"],
            end_state="main body/structure complete",
            forbidden_changes=["Workbench", "Lighting", "Camera angle", "Running gear"],
            input_mode=InputMode.PREVIOUS_FINAL_FRAME,
        ),
        ScenePlan(
            scene_id=5,
            name="Details & Systems",
            start_state="Scene 4 final frame",
            ordered_actions=[steps[min(5, len(steps)-1)] if len(steps) > 5 else "detail parts installed", "systems connected"],
            end_state="details and systems complete",
            forbidden_changes=["Workbench", "Lighting", "Camera angle", "Body structure"],
            input_mode=InputMode.PREVIOUS_FINAL_FRAME,
        ),
        ScenePlan(
            scene_id=6,
            name="Final Reveal",
            start_state="Scene 5 final frame",
            ordered_actions=[steps[-1], "all tools removed"],
            end_state="complete model revealed on clean workbench",
            forbidden_changes=["Workbench", "Lighting", "Camera angle", "Completed model"],
            input_mode=InputMode.PREVIOUS_FINAL_FRAME,
        ),
    ]


def make_first_frame_prompt(category: VehicleCategory, model_name: str) -> str:
    """Generate Master Image prompt for category — matches reference prompt skeleton exactly."""
    parts = VEHICLE_KEY_PARTS[category]
    return (
        f"Hyper-realistic macro photo of 100% disassembled miniature {model_name} model parts "
        f"neatly arranged on a wooden workbench, giant human hands only, no miniature people, "
        f"no small people, no tiny workers, no human figures, no characters, no completed model visible, "
        f"chassis/body/frame components, {parts} separated clearly, "
        f"tweezers, mini screwdriver, soft brush, nippers, 85mm lens, shallow depth of field, "
        f"8K product photo quality, bright workshop lighting, {model_name}, scene: Master Image."
    )


def make_scene_video_prompt(category: VehicleCategory, model_name: str, scene_id: int, scene_name: str) -> str:
    """Generate Video Prompt for specific scene — adapted from reference prompt 6-stage skeleton for multi-scene relay."""
    steps = VEHICLE_ASSEMBLY_STEPS[category]

    # Reference prompt base (exact wording from reference)
    base = (
        f"hyper-realistic macro ASMR assembly timelapse, giant human hands only, "
        f"no miniature people, no small people, no tiny workers, no human figures, no characters, "
        f"precise mechanical assembly logic, 100% disassembled parts to fully assembled model, "
        f"no floating or teleporting parts, parts attach in a realistic order and disappear from "
        f"workbench as installed, final step leaves only the fully assembled model on a clean "
        f"workbench, tweezers, mini screwdriver, soft brush, nippers, 85mm lens, shallow depth "
        f"of field, 8K product quality, bright workshop lighting, {model_name.lower()}, scene: {scene_name}. "
    )

    cleanup_rule = (
        "As parts are attached, they logically disappear from the workbench. "
        "By the final step, the workspace is completely clean, leaving only the fully assembled model. "
    )

    negative = f"Negative Prompt: {VEHICLE_NEGATIVE_BASE}."

    # Map scenes to reference's 6 stages
    if scene_id == 1:
        # Stage 1-2: Engine + Fasteners
        stage_desc = (
            f"Giant hands pick up engine block with tweezers and place it precisely into chassis. "
            f"Mini screwdriver rotates, tightening fasteners securing powertrain. "
            f"{steps[0]}. {steps[1] if len(steps) > 1 else ''}. "
        )
    elif scene_id == 2:
        # Stage 3-4: Wheels/Suspension + Steering
        stage_desc = (
            f"Hands mount wheels and suspension components onto chassis. "
            f"Steering rack installed and connected with precise alignment. "
            f"{steps[2] if len(steps) > 2 else ''}. {steps[3] if len(steps) > 3 else ''}. "
        )
    elif scene_id == 3:
        # Stage 5-6: Body Panels + Final Polish
        stage_desc = (
            f"External body panels fitted seamlessly onto frame. "
            f"Soft brush sweeps away dust, revealing pristine completed model on immaculate workbench. "
            f"{steps[4] if len(steps) > 4 else ''}. {steps[5] if len(steps) > 5 else ''}. "
        )
    else:
        # For 60s mode (6 scenes) - distribute 6 stages across 6 scenes
        stage_idx = scene_id - 1
        if stage_idx < len(steps):
            stage_desc = f"{steps[stage_idx]}. "
        else:
            stage_desc = "Assembly continues with precision. "

    return base + stage_desc + cleanup_rule + negative


# Alias for backward compatibility
make_video_prompt = make_scene_video_prompt


def make_style_bible(category: VehicleCategory, model_name: str) -> StyleBible:
    """Create StyleBible for category"""
    sb = VEHICLE_STYLE_BIBLES[category]
    return StyleBible(
        identity_lock=VEHICLE_IDENTITY_LOCKS[category],
        materials=sb["materials"],
        camera=sb["camera"],
        lighting=sb["lighting"],
        color_palette=sb["color_palette"],
        workspace=sb["workspace"],
        hands_rule=sb["hands_rule"],
        motion_rule=sb["motion_rule"],
        negative_prompt_base=VEHICLE_NEGATIVE_BASE,
    )


def get_categories() -> list[str]:
    return [c.value for c in VehicleCategory]


def get_models_for_category(category: str) -> list[str]:
    return VEHICLE_MODELS.get(VehicleCategory(category), [])


# Vehicle Assembly Profile export
vehicle_profile = Profile(
    profile_id="vehicle.assembly",
    version="2.0",
    topic_label="Vehicle Model Assembly",
    genre="vehicle",
    subtype="assembly",
    workflow_mode=WorkflowMode.REFERENCE_FRAME_RELAY,
    allowed_total_durations=[30, 60],
    default_total_duration=60,
    clip_duration_seconds=10,
    scene_plans=build_scene_plans_60s(VehicleCategory.CAR),  # placeholder, factory will override
    scene_plans_factory=lambda topic, dur, ctx: build_scene_plans_30s(ctx.get("vehicle_category")) if dur == 30 else build_scene_plans_60s(ctx.get("vehicle_category")),
    selection_schema={"vehicle_category": {"type": "string", "enum": [c.value for c in VehicleCategory], "required": True}, "model_name": {"type": "string", "required": True}},
    style_bible_factory=lambda topic, dur, ctx: make_style_bible(ctx["vehicle_category"], ctx["model_name"]),
    first_frame_factory=lambda topic, dur, ctx: {"first_frame_prompt": make_first_frame_prompt(ctx["vehicle_category"], ctx["model_name"])} if dur == 30 or ctx.get("scene_id") == 1 else {},
    scene_prompt_factory=lambda topic, dur, ctx: {"video_prompt": make_video_prompt(ctx["vehicle_category"], ctx["model_name"], ctx["scene_id"], ctx["scene_name"])},
    audio_contract=None,
    negative_prompt_base=VEHICLE_NEGATIVE_BASE,
    template_exclusions=["text, subtitle, caption, watermark, logo, burnt-in text, overlay text", "bad anatomy, deformed hands, blurry", "miniature people, small people, tiny workers, human figures, characters", "floating parts, teleporting parts, completed model at start"],
)

register_profile(vehicle_profile)


__all__ = [
    "VehicleCategory",
    "VEHICLE_MODELS",
    "VEHICLE_IDENTITY_LOCKS",
    "VEHICLE_KEY_PARTS",
    "VEHICLE_ASSEMBLY_STEPS",
    "VEHICLE_STYLE_BIBLES",
    "VEHICLE_NEGATIVE_BASE",
    "build_scene_plans_30s",
    "build_scene_plans_60s",
    "make_first_frame_prompt",
    "make_video_prompt",
    "make_style_bible",
    "get_categories",
    "get_models_for_category",
    "vehicle_profile",
]