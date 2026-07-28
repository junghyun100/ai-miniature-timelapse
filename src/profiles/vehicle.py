"""
Vehicle Assembly Profile — 10 Categories (car, motorcycle, airplane, boat, agricultural, helicopter, construction, spaceship, tank, bicycle)

Reference prompt based implementation per vehicle_assembly_reference.md
Each category has specific identity_lock, style_bible, scene_prompts, and assembly steps.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from ..profile_types import (
    InputMode,
    Profile,
    ScenePlan,
    StyleBible,
    WorkflowMode,
    register_profile,
)


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
    VehicleCategory.CAR: [
        "Porsche 911",
        "Ford Mustang",
        "Toyota 2000GT",
        "Ferrari 250 GTO",
        "Mini Cooper",
        "Volkswagen Beetle",
        "BMW 3.0 CSL",
        "Nissan Skyline GT-R",
        "Chevrolet Corvette",
        "Jaguar E-Type",
    ],
    VehicleCategory.MOTORCYCLE: [
        "Honda CB750",
        "Ducati 916",
        "Harley-Davidson Knucklehead",
        "Kawasaki Ninja ZX-10R",
        "BMW R nineT",
        "Triumph Bonneville",
        "Yamaha R1",
        "Moto Guzzi V7",
        "Indian Chief",
        "Royal Enfield Interceptor",
    ],
    VehicleCategory.AIRPLANE: [
        "Boeing 707",
        "Supermarine Spitfire",
        "P-51 Mustang",
        "F-16 Fighting Falcon",
        "Cessna 172",
        "SR-71 Blackbird",
        "Concorde",
        "F-22 Raptor",
        "Mitsubishi Zero",
        "B-17 Flying Fortress",
    ],
    VehicleCategory.BOAT: [
        "Chris-Craft Runabout",
        "America's Cup Yacht",
        "PT Boat",
        "U-Boat",
        "Titanic",
        "Viking Longship",
        "Sailing Frigate",
        "Speedboat",
        "Submarine",
        "Hovercraft",
    ],
    VehicleCategory.AGRICULTURAL: [
        "John Deere 4020",
        "Ford 8N",
        "Case IH Magnum",
        "Fendt 1050",
        "Massey Ferguson 135",
        "New Holland T8",
        "Claas Xerion",
        "Deutz-Fahr 9340",
        "Valtra S374",
        "Kubota M7",
    ],
    VehicleCategory.HELICOPTER: [
        "Bell 47",
        "UH-1 Huey",
        "AH-64 Apache",
        "Mi-24 Hind",
        "CH-47 Chinook",
        "Sikorsky S-76",
        "Robinson R44",
        "Eurocopter EC135",
        "Kamov Ka-50",
        "Boeing CH-47",
    ],
    VehicleCategory.CONSTRUCTION: [
        "Caterpillar D11",
        "Komatsu PC8000",
        "Liebherr R9800",
        "Hitachi EX8000",
        "Volvo EC950",
        "JCB 3CX",
        "Case 580",
        "Doosan DX225",
        "Hyundai R210",
        "Sumitomo SH350",
    ],
    VehicleCategory.SPACESHIP: [
        "Saturn V",
        "Falcon 9",
        "Space Shuttle",
        "Starship",
        "Soyuz",
        "Delta IV",
        "Ariane 5",
        "Atlas V",
        "Electron",
        "New Glenn",
    ],
    VehicleCategory.TANK: [
        "M1 Abrams",
        "T-90",
        "Leopard 2",
        "Challenger 2",
        "Type 99",
        "K2 Black Panther",
        "Merkava Mk 4",
        "T-14 Armata",
        "Panther",
        "Tiger I",
    ],
    VehicleCategory.BICYCLE: [
        "Pinarello Dogma",
        "Specialized S-Works",
        "Colnago C64",
        "Bianchi Oltre",
        "Cervélo R5",
        "Trek Madone",
        "Cannondale SuperSix",
        "Wilier Filante",
        "Factor Ostro",
        "Look 795",
    ],
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
        "engine mounts secured",
        "Wheels and suspension mounted",
        "Steering rack installed and connected",
        "Body panels fitted seamlessly",
        "Final polish revealing complete model on clean workbench",
    ],
    VehicleCategory.MOTORCYCLE: [
        "Engine lowered into frame cradle",
        "Bolts torqued securing engine to frame",
        "Wheels and suspension fitted",
        "Fork and handlebars assembled",
        "Tank, seat, and bodywork mounted",
        "Final polish revealing complete bike on clean workbench",
    ],
    VehicleCategory.AIRPLANE: [
        "Airframe skeleton and fuselage frame assembled",
        "Engine and cockpit mount secured",
        "Wings and tail attached",
        "Landing gear and control linkages installed",
        "Exterior panels, canopy, and propeller fitted",
        "Final polish revealing complete aircraft on clean workbench",
    ],
    VehicleCategory.BOAT: [
        "Engine installed in hull",
        "Mounts and fasteners secured",
        "Propeller shaft and rudder connected",
        "Steering and controls linked",
        "Deck, superstructure, and rigging fitted",
        "Final polish revealing complete vessel on clean workbench",
    ],
    VehicleCategory.AGRICULTURAL: [
        "Engine mounted to chassis",
        "Transmission and PTO bolted in place",
        "Wheels/tracks and suspension fitted",
        "Hydraulics and cab installed",
        "Drawbar and implement mounts attached",
        "Final polish revealing complete tractor on clean workbench",
    ],
    VehicleCategory.HELICOPTER: [
        "Main transmission and engine installed",
        "Mast and rotor head secured",
        "Tail boom and tail rotor fitted",
        "Landing skids and controls connected",
        "Fuselage panels and cockpit glazed",
        "Final polish revealing complete helicopter on clean workbench",
    ],
    VehicleCategory.CONSTRUCTION: [
        "Engine and hydraulic pump installed",
        "Tracks/wheels and final drives fitted",
        "Boom and arm structure assembled",
        "Bucket and hydraulic cylinders connected",
        "Cab and counterweight mounted",
        "Final polish revealing complete machine on clean workbench",
    ],
    VehicleCategory.SPACESHIP: [
        "Engines mounted to first stage",
        "Stage separation mechanisms secured",
        "Fuel tanks and plumbing installed",
        "Guidance and avionics integrated",
        "Payload fairing and grid fins fitted",
        "Final polish revealing complete rocket on clean workbench",
    ],
    VehicleCategory.TANK: [
        "Engine and transmission installed in hull",
        "Suspension and road wheels fitted",
        "Tracks connected and tensioned",
        "Turret ring and turret mounted",
        "Gun, optics, and armor fitted",
        "Final polish revealing complete tank on clean workbench",
    ],
    VehicleCategory.BICYCLE: [
        "Bottom bracket and cranks installed",
        "Drivetrain (chain, cassette, derailleurs) fitted",
        "Wheels trued and mounted",
        "Handlebars, stem, and controls assembled",
        "Saddle, seatpost, and brakes installed",
        "Final polish revealing complete bicycle on clean workbench",
    ],
}


def _coerce_category(category: VehicleCategory | str) -> VehicleCategory:
    if isinstance(category, VehicleCategory):
        return category
    return VehicleCategory(category)


def _category_label(category: VehicleCategory | str) -> str:
    return _coerce_category(category).value.replace("_", " ").title()


VEHICLE_SCENE_TITLES_30S: dict[VehicleCategory, list[str]] = {
    VehicleCategory.CAR: [
        "Foundation & Chassis",
        "Running Gear & Cabin",
        "Body Panels & Final Reveal",
    ],
    VehicleCategory.MOTORCYCLE: [
        "Frame & Engine",
        "Wheels, Fork & Controls",
        "Tank, Seat & Final Reveal",
    ],
    VehicleCategory.AIRPLANE: [
        "Airframe Skeleton & Engine Mount",
        "Wings, Tail, Landing Gear & Controls",
        "Exterior Panels, Canopy, Propeller & Final Reveal",
    ],
    VehicleCategory.BOAT: ["Hull & Engine", "Deck, Mast & Rigging", "Trim & Final Reveal"],
    VehicleCategory.AGRICULTURAL: [
        "Chassis & Engine",
        "Cab, Wheels & Hydraulics",
        "Implements & Final Reveal",
    ],
    VehicleCategory.HELICOPTER: [
        "Fuselage & Engine",
        "Rotor System & Skids",
        "Canopy & Final Reveal",
    ],
    VehicleCategory.CONSTRUCTION: [
        "Chassis & Hydraulics",
        "Boom, Arm & Tracks",
        "Cab & Final Reveal",
    ],
    VehicleCategory.SPACESHIP: [
        "Booster Core",
        "Stages, Tanks & Guidance",
        "Fairings & Final Reveal",
    ],
    VehicleCategory.TANK: ["Hull & Engine", "Suspension, Tracks & Turret", "Armor & Final Reveal"],
    VehicleCategory.BICYCLE: [
        "Frame & Drivetrain",
        "Wheels, Fork & Brakes",
        "Cockpit & Final Reveal",
    ],
}


VEHICLE_SCENE_TITLES_60S: dict[VehicleCategory, list[str]] = {
    VehicleCategory.CAR: [
        "Foundation & Chassis",
        "Engine & Powertrain",
        "Suspension & Steering",
        "Body Panels & Doors",
        "Paint & Trim",
        "Final Reveal",
    ],
    VehicleCategory.MOTORCYCLE: [
        "Frame & Engine",
        "Fasteners & Mounts",
        "Wheels & Fork",
        "Controls & Handlebars",
        "Bodywork & Paint",
        "Final Reveal",
    ],
    VehicleCategory.AIRPLANE: [
        "Airframe Skeleton & Engine Mount",
        "Wings & Tail",
        "Landing Gear & Controls",
        "Exterior Panels",
        "Canopy, Propeller & Paint",
        "Final Reveal",
    ],
    VehicleCategory.BOAT: [
        "Hull & Keel",
        "Engine & Propulsion",
        "Deck & Mast",
        "Rigging & Railings",
        "Paint & Finish",
        "Final Reveal",
    ],
    VehicleCategory.AGRICULTURAL: [
        "Chassis & Engine",
        "Transmission & Wheels",
        "Cab & Hydraulics",
        "Implements & Controls",
        "Paint & Decals",
        "Final Reveal",
    ],
    VehicleCategory.HELICOPTER: [
        "Fuselage & Engine",
        "Rotor System",
        "Tail Boom & Rotor",
        "Skids & Controls",
        "Canopy & Paint",
        "Final Reveal",
    ],
    VehicleCategory.CONSTRUCTION: [
        "Chassis & Engine",
        "Boom & Arm",
        "Tracks & Suspension",
        "Hydraulics & Controls",
        "Cab & Counterweight",
        "Final Reveal",
    ],
    VehicleCategory.SPACESHIP: [
        "Booster Core",
        "Engines & Tanks",
        "Guidance & Separation",
        "Fins & Fairings",
        "Paint & Markings",
        "Final Reveal",
    ],
    VehicleCategory.TANK: [
        "Hull & Engine",
        "Suspension & Tracks",
        "Turret & Gun",
        "Armor & Optics",
        "Paint & Weathering",
        "Final Reveal",
    ],
    VehicleCategory.BICYCLE: [
        "Frame & Drivetrain",
        "Wheels & Brakes",
        "Handlebars & Controls",
        "Saddle & Fitments",
        "Paint & Decals",
        "Final Reveal",
    ],
}


VEHICLE_COMPLETION_RANGES_30S = ["0-30%", "30-75%", "75-100%"]
VEHICLE_COMPLETION_RANGES_60S = ["0-15%", "15-35%", "35-55%", "55-75%", "75-90%", "90-100%"]


def _ordered_action_groups(category: VehicleCategory, duration_seconds: int) -> list[list[str]]:
    steps = VEHICLE_ASSEMBLY_STEPS[category]
    if duration_seconds == 30:
        return [steps[:2], steps[2:4], steps[4:6]]
    return [[step] for step in steps[:6]]


def _scene_titles(category: VehicleCategory, duration_seconds: int) -> list[str]:
    if duration_seconds == 30:
        return VEHICLE_SCENE_TITLES_30S[category]
    return VEHICLE_SCENE_TITLES_60S[category]


def _completion_ranges(duration_seconds: int) -> list[str]:
    return (
        VEHICLE_COMPLETION_RANGES_30S if duration_seconds == 30 else VEHICLE_COMPLETION_RANGES_60S
    )


def _reserved_future_actions(action_groups: list[list[str]], scene_index: int) -> list[str]:
    future_actions: list[str] = []
    for group in action_groups[scene_index + 1 :]:
        future_actions.extend(group)
    return future_actions


def _forbidden_future_actions(reserved_actions: list[str]) -> list[str]:
    return [
        f"Do not perform this later-stage action in the current scene: {action}"
        for action in reserved_actions
    ]


def _sanitize_reserved_future_action(action: str) -> str:
    lowered = action.lower()
    if any(
        token in lowered
        for token in (
            "final polish",
            "final reveal",
            "clean workbench",
            "hero reveal",
            "final finish",
        )
    ):
        return "later finishing stage"
    return action


def _sanitize_reserved_future_actions(reserved_actions: list[str]) -> list[str]:
    sanitized: list[str] = []
    for action in reserved_actions:
        cleaned_action = _sanitize_reserved_future_action(action)
        if cleaned_action not in sanitized:
            sanitized.append(cleaned_action)
    return sanitized


def _summarize_actions(actions: list[str]) -> str:
    return "; ".join(action for action in actions if action)


def _summarize_reserved_future_actions(reserved_actions: list[str]) -> str:
    return ", ".join(reserved_actions[:3]) if reserved_actions else "no remaining actions"


def _scene_start_state(
    scene_index: int,
    duration_seconds: int,
    category: VehicleCategory,
    previous_stop_state: str | None,
) -> str:
    label = _category_label(category)
    if scene_index == 0:
        return f"Empty workbench with all {label.lower()} parts disassembled and ready for the first placement."
    return previous_stop_state or f"Scene {scene_index} final frame"


def _scene_end_state(
    *,
    scene_name: str,
    ordered_actions: list[str],
    reserved_future_actions: list[str],
    is_final_scene: bool,
    category: VehicleCategory,
) -> str:
    label = _category_label(category)
    if is_final_scene:
        return f"Fully assembled {label.lower()} model revealed on a clean workbench."
    completed_summary = _summarize_actions(ordered_actions) or scene_name
    future_summary = _summarize_reserved_future_actions(reserved_future_actions)
    return (
        f"Completed actions in this scene: {completed_summary}. "
        f"The {label.lower()} remains visibly incomplete, with future parts still separate, visible, and unused: "
        f"{future_summary}."
    )


def _scene_exact_stop_state(
    *,
    scene_name: str,
    ordered_actions: list[str],
    reserved_future_actions: list[str],
    is_final_scene: bool,
    category: VehicleCategory,
) -> str:
    label = _category_label(category)
    if is_final_scene:
        return (
            f"Final reveal only: the fully assembled {label.lower()} model sits alone on a clean workbench "
            f"after the final polish."
        )
    completed_summary = _summarize_actions(ordered_actions) or scene_name
    future_summary = _summarize_reserved_future_actions(
        _sanitize_reserved_future_actions(reserved_future_actions)
    )
    return (
        f"Exact stop state after this scene's completed actions: {completed_summary}. "
        f"The {label.lower()} must remain visibly incomplete, with future parts still separate, visible, and unused: "
        f"{future_summary}."
    )


def _build_scene_plans(category: VehicleCategory, duration_seconds: int) -> list[ScenePlan]:
    category = _coerce_category(category)
    action_groups = _ordered_action_groups(category, duration_seconds)
    titles = _scene_titles(category, duration_seconds)
    ranges = _completion_ranges(duration_seconds)

    plans: list[ScenePlan] = []
    previous_stop_state: str | None = None
    for index, (scene_name, ordered_actions, completion_range) in enumerate(
        zip(titles, action_groups, ranges)
    ):
        is_final_scene = index == len(action_groups) - 1
        reserved_actions = _sanitize_reserved_future_actions(
            _reserved_future_actions(action_groups, index)
        )
        forbidden_actions = _forbidden_future_actions(reserved_actions)
        end_state = _scene_end_state(
            scene_name=scene_name,
            ordered_actions=ordered_actions,
            reserved_future_actions=reserved_actions,
            is_final_scene=is_final_scene,
            category=category,
        )
        exact_stop_state = _scene_exact_stop_state(
            scene_name=scene_name,
            ordered_actions=ordered_actions,
            reserved_future_actions=reserved_actions,
            is_final_scene=is_final_scene,
            category=category,
        )
        start_state = _scene_start_state(index, duration_seconds, category, previous_stop_state)
        forbidden_changes = [
            "Camera angle",
            "Lighting",
            "Workbench layout",
            "Camera scale",
            "Model identity",
        ]

        plans.append(
            ScenePlan(
                scene_id=index + 1,
                name=scene_name,
                start_state=start_state,
                ordered_actions=ordered_actions,
                end_state=exact_stop_state,
                forbidden_changes=forbidden_changes,
                input_mode=InputMode.MASTER_IMAGE if index == 0 else InputMode.PREVIOUS_FINAL_FRAME,
                estimated_clip_duration_seconds=10,
                completion_range=completion_range,
                is_final_scene=is_final_scene,
                reserved_future_actions=reserved_actions,
                forbidden_future_actions=forbidden_actions,
                exact_stop_state=exact_stop_state,
            )
        )
        previous_stop_state = exact_stop_state

    return plans


def build_scene_plans_30s(category: VehicleCategory | str) -> list[ScenePlan]:
    """3 scenes for 30s total (3 x 10s)."""
    return _build_scene_plans(_coerce_category(category), 30)


def build_scene_plans_60s(category: VehicleCategory | str) -> list[ScenePlan]:
    """6 scenes for 60s total (6 x 10s)."""
    return _build_scene_plans(_coerce_category(category), 60)


# Style Bible per category
VEHICLE_STYLE_BIBLES: dict[VehicleCategory, dict[str, Any]] = {
    VehicleCategory.CAR: {
        "materials": {
            "primary": ["die-cast metal", "plastic", "rubber tires", "clear plastic glass"],
            "secondary": ["paint", "chrome", "decals"],
            "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "file", "cement"],
        },
        "camera": {
            "lens": "85mm",
            "angle": "macro_closeup",
            "movement": "fixed",
            "distance": "macro",
        },
        "lighting": {
            "key": "bright workshop overhead",
            "fill": "soft diffuser",
            "mood": "bright_clean",
            "consistency": "locked",
        },
        "color_palette": {
            "primary": ["metallic silver", "gunmetal", "chrome"],
            "accent": ["model-specific paint"],
            "background": "clean workbench surface",
            "tone": "cool_cinematic",
        },
        "workspace": {
            "surface": "wooden workbench",
            "environment": "bright workshop",
            "clutter_rule": "parts_disappear",
        },
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.MOTORCYCLE: {
        "materials": {
            "primary": ["die-cast metal", "plastic", "rubber tires", "chrome"],
            "secondary": ["paint", "decals", "leather seat"],
            "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "torque wrench"],
        },
        "camera": {
            "lens": "85mm",
            "angle": "macro_closeup",
            "movement": "fixed",
            "distance": "macro",
        },
        "lighting": {
            "key": "bright workshop overhead",
            "fill": "soft diffuser",
            "mood": "bright_clean",
            "consistency": "locked",
        },
        "color_palette": {
            "primary": ["metallic silver", "chrome", "black"],
            "accent": ["model-specific paint"],
            "background": "clean workbench surface",
            "tone": "cool_cinematic",
        },
        "workspace": {
            "surface": "wooden workbench",
            "environment": "bright workshop",
            "clutter_rule": "parts_disappear",
        },
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.AIRPLANE: {
        "materials": {
            "primary": ["die-cast metal", "plastic", "rubber tires"],
            "secondary": ["paint", "decals", "panel lines"],
            "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "pin vise"],
        },
        "camera": {
            "lens": "85mm",
            "angle": "macro_closeup",
            "movement": "fixed",
            "distance": "macro",
        },
        "lighting": {
            "key": "bright workshop overhead",
            "fill": "soft diffuser",
            "mood": "bright_clean",
            "consistency": "locked",
        },
        "color_palette": {
            "primary": ["metallic silver", "aluminum", "olive drab"],
            "accent": ["model-specific markings"],
            "background": "clean workbench surface",
            "tone": "cool_cinematic",
        },
        "workspace": {
            "surface": "wooden workbench",
            "environment": "bright workshop",
            "clutter_rule": "parts_disappear",
        },
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.BOAT: {
        "materials": {
            "primary": ["die-cast metal", "plastic", "wood", "fabric sails"],
            "secondary": ["paint", "varnish", "rigging"],
            "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "needle"],
        },
        "camera": {
            "lens": "85mm",
            "angle": "macro_closeup",
            "movement": "fixed",
            "distance": "macro",
        },
        "lighting": {
            "key": "bright workshop overhead",
            "fill": "soft diffuser",
            "mood": "bright_clean",
            "consistency": "locked",
        },
        "color_palette": {
            "primary": ["white", "navy", "wood tones"],
            "accent": ["brass", "copper"],
            "background": "clean workbench surface",
            "tone": "cool_cinematic",
        },
        "workspace": {
            "surface": "wooden workbench",
            "environment": "bright workshop",
            "clutter_rule": "parts_disappear",
        },
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.AGRICULTURAL: {
        "materials": {
            "primary": ["die-cast metal", "plastic", "rubber tires/tracks"],
            "secondary": ["paint", "decals", "hydraulic hoses"],
            "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "wrench"],
        },
        "camera": {
            "lens": "85mm",
            "angle": "macro_closeup",
            "movement": "fixed",
            "distance": "macro",
        },
        "lighting": {
            "key": "bright workshop overhead",
            "fill": "soft diffuser",
            "mood": "bright_clean",
            "consistency": "locked",
        },
        "color_palette": {
            "primary": ["green", "red", "yellow", "blue"],
            "accent": ["chrome", "black"],
            "background": "clean workbench surface",
            "tone": "cool_cinematic",
        },
        "workspace": {
            "surface": "wooden workbench",
            "environment": "bright workshop",
            "clutter_rule": "parts_disappear",
        },
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.HELICOPTER: {
        "materials": {
            "primary": ["die-cast metal", "plastic", "composite rotor blades"],
            "secondary": ["paint", "decals", "clear canopy"],
            "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "pin vise"],
        },
        "camera": {
            "lens": "85mm",
            "angle": "macro_closeup",
            "movement": "fixed",
            "distance": "macro",
        },
        "lighting": {
            "key": "bright workshop overhead",
            "fill": "soft diffuser",
            "mood": "bright_clean",
            "consistency": "locked",
        },
        "color_palette": {
            "primary": ["olive drab", "gray", "camouflage"],
            "accent": ["red cross", "warning stripes"],
            "background": "clean workbench surface",
            "tone": "cool_cinematic",
        },
        "workspace": {
            "surface": "wooden workbench",
            "environment": "bright workshop",
            "clutter_rule": "parts_disappear",
        },
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.CONSTRUCTION: {
        "materials": {
            "primary": ["die-cast metal", "plastic", "rubber tracks/tires"],
            "secondary": ["paint", "decals", "hydraulic hoses"],
            "tools": [
                "tweezers",
                "mini screwdriver",
                "soft brush",
                "nippers",
                "wrench",
                "allen keys",
            ],
        },
        "camera": {
            "lens": "85mm",
            "angle": "macro_closeup",
            "movement": "fixed",
            "distance": "macro",
        },
        "lighting": {
            "key": "bright workshop overhead",
            "fill": "soft diffuser",
            "mood": "bright_clean",
            "consistency": "locked",
        },
        "color_palette": {
            "primary": ["yellow", "orange", "gray"],
            "accent": ["black tracks", "chrome"],
            "background": "clean workbench surface",
            "tone": "cool_cinematic",
        },
        "workspace": {
            "surface": "wooden workbench",
            "environment": "bright workshop",
            "clutter_rule": "parts_disappear",
        },
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.SPACESHIP: {
        "materials": {
            "primary": ["die-cast metal", "plastic", "composite"],
            "secondary": ["paint", "thermal tiles", "decals"],
            "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "torque wrench"],
        },
        "camera": {
            "lens": "85mm",
            "angle": "macro_closeup",
            "movement": "fixed",
            "distance": "macro",
        },
        "lighting": {
            "key": "bright workshop overhead",
            "fill": "soft diffuser",
            "mood": "bright_clean",
            "consistency": "locked",
        },
        "color_palette": {
            "primary": ["white", "black", "metallic"],
            "accent": ["engine glow", "grid fins"],
            "background": "clean workbench surface",
            "tone": "cool_cinematic",
        },
        "workspace": {
            "surface": "wooden workbench",
            "environment": "bright workshop",
            "clutter_rule": "parts_disappear",
        },
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.TANK: {
        "materials": {
            "primary": ["die-cast metal", "plastic", "rubber/metal tracks"],
            "secondary": ["paint", "decals", "photo-etched parts"],
            "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "file", "cement"],
        },
        "camera": {
            "lens": "85mm",
            "angle": "macro_closeup",
            "movement": "fixed",
            "distance": "macro",
        },
        "lighting": {
            "key": "bright workshop overhead",
            "fill": "soft diffuser",
            "mood": "bright_clean",
            "consistency": "locked",
        },
        "color_palette": {
            "primary": ["olive drab", "sand", "gray", "camouflage"],
            "accent": ["gun metal", "glass"],
            "background": "clean workbench surface",
            "tone": "cool_cinematic",
        },
        "workspace": {
            "surface": "wooden workbench",
            "environment": "bright workshop",
            "clutter_rule": "parts_disappear",
        },
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
    VehicleCategory.BICYCLE: {
        "materials": {
            "primary": ["carbon fiber", "aluminum", "steel", "rubber tires"],
            "secondary": ["paint", "decals", "bar tape"],
            "tools": [
                "tweezers",
                "mini screwdriver",
                "soft brush",
                "nippers",
                "chain tool",
                "allen keys",
            ],
        },
        "camera": {
            "lens": "85mm",
            "angle": "macro_closeup",
            "movement": "fixed",
            "distance": "macro",
        },
        "lighting": {
            "key": "bright workshop overhead",
            "fill": "soft diffuser",
            "mood": "bright_clean",
            "consistency": "locked",
        },
        "color_palette": {
            "primary": ["carbon black", "metallic team colors"],
            "accent": ["chrome", "anodized"],
            "background": "clean workbench surface",
            "tone": "cool_cinematic",
        },
        "workspace": {
            "surface": "wooden workbench",
            "environment": "bright workshop",
            "clutter_rule": "parts_disappear",
        },
        "hands_rule": "giant_hands_with_tools",
        "motion_rule": "stop_motion_assembly",
    },
}

# Immutable negative prompt (fixed per spec — matches reference prompt exactly)
VEHICLE_NEGATIVE_BASE = "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry."


def make_first_frame_prompt(category: VehicleCategory, model_name: str) -> str:
    """Generate Master Image prompt for category."""
    category = _coerce_category(category)
    parts = VEHICLE_KEY_PARTS[category]
    return (
        f"Hyper-realistic macro photo of 100% disassembled miniature {model_name} model parts "
        f"neatly arranged on a wooden workbench, giant human hands only, no miniature people, "
        f"no small people, no tiny workers, no human figures, no characters, no completed model visible, "
        f"chassis/body/frame components, {parts} separated clearly, "
        f"tweezers, mini screwdriver, soft brush, nippers, 85mm lens, shallow depth of field, "
        f"8K product photo quality, bright workshop lighting, {model_name}, scene: Master Image."
    )


def _resolve_scene_plan(
    category: VehicleCategory,
    scene_id: int,
    scene_name: str,
    scene_plan: ScenePlan | None = None,
    total_duration: int | None = None,
) -> ScenePlan:
    category = _coerce_category(category)
    if scene_plan is not None:
        return scene_plan

    duration_hint = total_duration if total_duration in {30, 60} else (60 if scene_id > 3 else 30)
    plans = (
        build_scene_plans_60s(category) if duration_hint == 60 else build_scene_plans_30s(category)
    )
    if 1 <= scene_id <= len(plans):
        return plans[scene_id - 1]

    is_final_scene = "final" in scene_name.lower() or "reveal" in scene_name.lower()
    start_state = (
        "all parts disassembled on workbench"
        if scene_id == 1
        else f"Scene {scene_id - 1} final frame"
    )
    ordered_actions = VEHICLE_ASSEMBLY_STEPS[category][:1]
    reserved_future_actions = []
    exact_stop_state = (
        "Final reveal only: the fully assembled model sits alone on a clean workbench after the final polish."
        if is_final_scene
        else "Stop immediately when the current stage is finished. The model must remain visibly incomplete."
    )
    return ScenePlan(
        scene_id=scene_id,
        name=scene_name,
        start_state=start_state,
        ordered_actions=ordered_actions,
        end_state=exact_stop_state,
        forbidden_changes=["Camera angle", "Lighting", "Workbench layout"],
        input_mode=InputMode.MASTER_IMAGE if scene_id == 1 else InputMode.PREVIOUS_FINAL_FRAME,
        completion_range="0-30%" if scene_id == 1 else "30-75%" if scene_id == 2 else "75-100%",
        is_final_scene=is_final_scene,
        reserved_future_actions=reserved_future_actions,
        forbidden_future_actions=[],
        exact_stop_state=exact_stop_state,
    )


def make_scene_video_prompt(
    category: VehicleCategory,
    model_name: str,
    scene_id: int,
    scene_name: str,
    scene_plan: ScenePlan | None = None,
    total_duration: int | None = None,
) -> str:
    """Generate a scene-bounded video prompt that stops before the next scene."""
    category = _coerce_category(category)
    resolved_plan = _resolve_scene_plan(category, scene_id, scene_name, scene_plan, total_duration)
    model_lower = model_name.lower()
    reserved_future_actions = _sanitize_reserved_future_actions(
        resolved_plan.reserved_future_actions
    )
    reserved_future_clause = (
        f"Prohibited future work: {', '.join(reserved_future_actions)}."
        if reserved_future_actions
        else "Prohibited future work: none remain."
    )
    current_actions = _summarize_actions(resolved_plan.ordered_actions)

    core_rules = (
        "hyper-realistic macro ASMR assembly timelapse, giant human hands only, "
        "no miniature people, no small people, no tiny workers, no human figures, no characters, "
        "precise mechanical assembly logic, no floating or teleporting parts, "
        "parts attach in realistic order and disappear from the workbench as installed, "
        "tweezers, mini screwdriver, soft brush, nippers, 85mm lens, shallow depth of field, "
        "8K product quality, bright workshop lighting"
    )

    ordered_actions = current_actions or "continue the current build step"

    if resolved_plan.is_final_scene:
        body = " ".join(
            [
                f"{core_rules}, {model_lower}, scene: {resolved_plan.name}.",
                f"Completion range: {resolved_plan.completion_range}.",
                f"Exact input/start state: {resolved_plan.start_state}.",
                f"Ordered current actions: {ordered_actions}.",
                f"Exact stop state: {resolved_plan.exact_stop_state}.",
                "Final-only permissions: final polish, cleanup, and hero reveal are allowed only here.",
                "Maintain the same camera angle, scale, lighting direction, and workbench layout throughout.",
                "Hands only. No floating or teleporting parts.",
                f"Negative Prompt: {VEHICLE_NEGATIVE_BASE}",
            ]
        )
        return body

    body = " ".join(
        [
            f"{core_rules}, {model_lower}, scene: {resolved_plan.name}.",
            f"Completion range: {resolved_plan.completion_range}.",
            f"Exact input/start state: {resolved_plan.start_state}.",
            f"Ordered current actions: {ordered_actions}.",
            f"Exact stop state: {resolved_plan.exact_stop_state}.",
            reserved_future_clause,
            "The model must remain visibly incomplete, with future parts still separate, visible, and unused.",
            "Do not proceed beyond this stop state.",
            "Maintain the same camera angle, scale, lighting direction, and workbench layout throughout.",
            "Hands only. No floating or teleporting parts.",
            f"Negative Prompt: {VEHICLE_NEGATIVE_BASE}",
        ]
    )
    return body


# Alias for backward compatibility
make_video_prompt = make_scene_video_prompt


def make_style_bible(category: VehicleCategory, model_name: str) -> StyleBible:
    """Create StyleBible for category"""
    category = _coerce_category(category)
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
    return VEHICLE_MODELS.get(_coerce_category(category), [])


VEHICLE_SELECTION_SCHEMA = {
    "type": "object",
    "title": "Vehicle Assembly Options",
    "required": ["vehicle_category", "model_name"],
    "properties": {
        "vehicle_category": {
            "type": "string",
            "title": "Vehicle category",
            "enum": [category.value for category in VehicleCategory],
            "x-enum-labels": [
                category.value.replace("_", " ").title() for category in VehicleCategory
            ],
        },
        "model_name": {
            "type": "string",
            "title": "Model",
            "minLength": 1,
            "x-dependent-options": {
                "field": "vehicle_category",
                "options": {category.value: models for category, models in VEHICLE_MODELS.items()},
            },
        },
    },
    "x-ui-order": ["vehicle_category", "model_name"],
}


# Vehicle Assembly Profile export
vehicle_profile = Profile(
    profile_id="vehicle.assembly",
    version="2.0",
    topic_label="Vehicle Model Assembly",
    genre="vehicle",
    subtype="assembly",
    workflow_mode=WorkflowMode.REFERENCE_FRAME_RELAY,
    allowed_total_durations=[30, 60],
    default_total_duration=30,
    clip_duration_seconds=10,
    scene_plans=build_scene_plans_30s(VehicleCategory.CAR),  # placeholder, factory will override
    scene_plans_factory=lambda topic, dur, ctx: (
        build_scene_plans_30s(ctx.get("vehicle_category"))
        if dur == 30
        else build_scene_plans_60s(ctx.get("vehicle_category"))
    ),
    selection_schema=VEHICLE_SELECTION_SCHEMA,
    style_bible_factory=lambda topic, dur, ctx: make_style_bible(
        ctx["vehicle_category"], ctx["model_name"]
    ),
    first_frame_factory=lambda topic, dur, ctx: (
        {"first_frame_prompt": make_first_frame_prompt(ctx["vehicle_category"], ctx["model_name"])}
        if ctx.get("scene_id") == 1
        else {}
    ),
    scene_prompt_factory=lambda topic, dur, ctx: {
        "video_prompt": make_video_prompt(
            ctx["vehicle_category"],
            ctx["model_name"],
            ctx["scene_id"],
            ctx["scene_name"],
            ctx.get("scene_plan"),
            dur,
        )
    },
    audio_contract={
        "type": "asmr_only",
        "description": "Hands-only assembly sounds. No voices, no music.",
    },
    negative_prompt_base=VEHICLE_NEGATIVE_BASE,
    template_exclusions=[
        "text, subtitle, caption, watermark, logo, burnt-in text, overlay text",
        "bad anatomy, deformed hands, blurry",
        "miniature people, small people, tiny workers, human figures, characters",
        "floating parts, teleporting parts, completed model at start",
    ],
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
