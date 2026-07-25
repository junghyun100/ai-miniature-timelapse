"""
Vehicle Assembly Profile (vehicle.assembly)

Per Section 13.6:
- Workflow: SINGLE_CLIP_FROM_MASTER
- Duration: 10s (single clip)
- 10 categories with specific models
- 6-stage assembly sequence
- Parts disappear as assembled
"""

from enum import Enum
from ..profile_types import (
    Profile, ScenePlan, WorkflowMode, StyleBible, InputMode, register_profile
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


# Category -> Model suggestions (Table 13.6)
VEHICLE_MODELS = {
    VehicleCategory.CAR: [
        "Porsche 911", "Ford Mustang", "Ferrari F40", "Lamborghini Countach",
        "BMW M3 E30", "Toyota Supra MK4", "Mazda RX-7", "Honda NSX",
        "Chevrolet Corvette C2", "Volkswagen Beetle"
    ],
    VehicleCategory.MOTORCYCLE: [
        "Honda CB750", "Ducati 916", "Harley-Davidson Fat Boy", "Kawasaki Ninja ZX-10R",
        "BMW R1200GS", "Triumph Bonneville", "Yamaha YZF-R1", "Suzuki Hayabusa",
        "Royal Enfield Classic", "Vespa Primavera"
    ],
    VehicleCategory.AIRPLANE: [
        "Spitfire Mk IX", "P-51 Mustang", "F-14 Tomcat", "F-22 Raptor",
        "Boeing 747", "Concorde", "SR-71 Blackbird", "Cessna 172",
        "Wright Flyer", "Messerschmitt Bf 109"
    ],
    VehicleCategory.BOAT: [
        "America's Cup Yacht", "Titanic", "U-Boat Type VII", "PT Boat",
        "Chris-Craft Runabout", "Sailboat Optimist", "Kayak", "Gondola",
        "Viking Longship", "Aircraft Carrier"
    ],
    VehicleCategory.AGRICULTURAL: [
        "John Deere 8R Tractor", "Case IH Combine", "New Holland Baler",
        "CLAAS Jaguar", "Fendt 1050", "Kubota M7", "Massey Ferguson 8S",
        "Deutz-Fahr 9 Series", "Valtra S Series", "JCB Fastrac"
    ],
    VehicleCategory.HELICOPTER: [
        "Bell UH-1 Huey", "Boeing AH-64 Apache", "Sikorsky UH-60 Black Hawk",
        "Eurocopter Tiger", "Mil Mi-24 Hind", "Robinson R44", "Bell 407",
        "Airbus H145", "Kaman K-MAX", "Sikorsky CH-53"
    ],
    VehicleCategory.CONSTRUCTION: [
        "Caterpillar D11 Dozer", "Komatsu PC8000 Excavator", "Liebherr LR 13000 Crane",
        "Volvo A60H Hauler", "Hitachi EX8000", "Terex MT 6300AC", "Bucyrus RH400",
        "Liebherr R 9800", "Caterpillar 797F", "Komatsu 980E"
    ],
    VehicleCategory.SPACESHIP: [
        "Saturn V", "Space Shuttle", "Falcon 9", "Starship",
        "Soyuz", "Apollo CSM", "Lunar Module", "ISS Module",
        "Voyager Probe", "James Webb Telescope"
    ],
    VehicleCategory.TANK: [
        "M1 Abrams", "Leopard 2A7", "T-14 Armata", "Challenger 2",
        "Type 99", "K2 Black Panther", "Merkava Mk 4", "T-90M",
        "Leclerc", "VT-4"
    ],
    VehicleCategory.BICYCLE: [
        "Pinarello Dogma F", "Specialized S-Works Tarmac", "Trek Madone SLR",
        "Canyon Aeroad", "Cervelo R5", "Bianchi Oltre XR4", "Colnago V4Rs",
        "Scott Foil RC", "Factor Ostro VAM", "Wilier Filante SLR"
    ],
}


VEHICLE_IDENTITY_LOCK = (
    "hyper-realistic macro ASMR assembly timelapse, giant human hands only, "
    "no miniature people, no small people, no tiny workers, no human figures, "
    "no characters, precise mechanical assembly logic, 100% disassembled parts "
    "to fully assembled model, no floating or teleporting parts, parts attach "
    "in realistic order and disappear from workbench as installed, final step "
    "leaves only the fully assembled model on a clean workbench, tweezers, "
    "mini screwdriver, soft brush, nippers, 85mm lens, shallow depth of field, "
    "8K product quality, bright workshop lighting"
)


VEHICLE_NEGATIVE_BASE = (
    "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, "
    "bad anatomy, deformed hands, blurry, miniature people, tiny workers, "
    "small people, human figures, characters, floating parts, teleporting parts, "
    "completed model at start"
)


# Single scene plan (10s)
SCENE_PLAN = [
    ScenePlan(
        scene_id=1,
        name="Assembly",
        start_state="Disassembled parts on workbench",
        ordered_actions=[
            "Engine/chassis placed on workbench",
            "Major sub-assemblies built (engine, drivetrain, suspension)",
            "Sub-assemblies joined to chassis",
            "Wheels/tracks/landing gear attached",
            "Body panels/skin installed",
            "Final detailing and cleanup",
        ],
        end_state="Fully assembled model alone on clean workbench",
        forbidden_changes=[
            "Camera angle", "Lighting", "Workbench surface", "Tool positions",
            "Parts must not float/teleport", "Completed model cannot appear before final step"
        ],
        input_mode=InputMode.MASTER_IMAGE,
        estimated_clip_duration_seconds=10,
    ),
]


VEHICLE_SELECTION_SCHEMA = {
    "type": "object",
    "required": ["subtype", "model_name"],
    "properties": {
        "subtype": {"type": "string", "enum": [c.value for c in VehicleCategory]},
        "model_name": {"type": "string", "minLength": 1},
    },
}


vehicle_profile = Profile(
    profile_id="vehicle.assembly",
    version="2.0.0",
    topic_label="Vehicle Assembly",
    workflow_mode=WorkflowMode.SINGLE_CLIP_FROM_MASTER,
    allowed_total_durations=[10],
    default_total_duration=10,
    clip_duration_seconds=10,
    scene_plans=SCENE_PLAN,
    selection_schema=VEHICLE_SELECTION_SCHEMA,
    style_bible_factory={},
    first_frame_factory={},
    scene_prompt_factory={},
    audio_contract={
        "type": "asmr_only",
        "description": "Mechanical clicks, screw turns, part seating sounds. No voices, no music."
    },
    negative_prompt_base=VEHICLE_NEGATIVE_BASE,
    template_exclusions=["completed model at start", "floating parts", "teleporting parts"],
)

register_profile(vehicle_profile)


def make_style_bible(subtype: str, model_name: str) -> StyleBible:
    return StyleBible(
        identity_lock=VEHICLE_IDENTITY_LOCK,
        materials={
            "primary": ["die-cast metal", "plastic", "photo-etched brass", "rubber tires"],
            "secondary": ["paint", "decals", "chrome plating", "clear coat"],
            "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "file", "cement"],
        },
        camera={
            "lens": "85mm",
            "angle": "macro_closeup",
            "movement": "fixed",
            "distance": "macro",
        },
        lighting={
            "key": "bright workshop overhead",
            "fill": "soft diffuser",
            "mood": "bright_clean",
            "consistency": "locked",
        },
        color_palette={
            "primary": ["metallic silver", "gunmetal", "chrome"],
            "accent": ["model-specific paint colors"],
            "background": "clean workbench surface",
            "tone": "cool_cinematic",
        },
        workspace={
            "surface": "wooden workbench",
            "environment": "bright workshop",
            "clutter_rule": "parts_disappear",
        },
        hands_rule="giant_hands_with_tools",
        motion_rule="stop_motion_assembly",
        negative_prompt_base=VEHICLE_NEGATIVE_BASE,
    )


def make_first_frame_prompt(subtype: str, model_name: str) -> str:
    category = VehicleCategory(subtype)
    models = VEHICLE_MODELS[category]
    key_parts = {
        VehicleCategory.CAR: "chassis, engine block, transmission, suspension, wheels, body panels, steering",
        VehicleCategory.MOTORCYCLE: "engine, frame, wheels, fork, swingarm, tank, exhaust",
        VehicleCategory.AIRPLANE: "fuselage, wings, engine, propeller/jet, landing gear, tail, cockpit",
        VehicleCategory.BOAT: "hull, deck, mast/superstructure, engine, propeller, rudder, anchor",
        VehicleCategory.AGRICULTURAL: "engine, transmission, chassis, wheels/tracks, PTO, hydraulics, cab",
        VehicleCategory.HELICOPTER: "main rotor, tail rotor, engine, transmission, fuselage, landing skids, cockpit",
        VehicleCategory.CONSTRUCTION: "tracks/wheels, chassis, engine, hydraulic system, boom/arm, bucket, cab",
        VehicleCategory.SPACESHIP: "stages, engines, fuel tanks, payload fairing, guidance, heat shield, landing legs",
        VehicleCategory.TANK: "hull, turret, gun, tracks, engine, transmission, suspension",
        VehicleCategory.BICYCLE: "frame, fork, wheels, drivetrain, handlebars, saddle, brakes",
    }
    parts = key_parts[category]
    return (
        f"Hyper-realistic macro photo of 100% disassembled miniature {model_name} model parts "
        f"neatly arranged on a wooden workbench, giant human hands only, no miniature people, "
        f"no small people, no tiny workers, no human figures, no characters, no completed model visible, "
        f"chassis/body/frame components, {parts} separated clearly, "
        f"tweezers, mini screwdriver, soft brush, nippers, 85mm lens, shallow depth of field, "
        f"8K product photo quality, bright workshop lighting, {model_name}, scene: Master Image."
    )


def make_scene_video_prompt(subtype: str, model_name: str) -> str:
    category = VehicleCategory(subtype)
    key_parts = {
        VehicleCategory.CAR: "chassis, engine block, transmission, suspension, wheels, body panels, steering",
        VehicleCategory.MOTORCYCLE: "engine, frame, wheels, fork, swingarm, tank, exhaust",
        VehicleCategory.AIRPLANE: "fuselage, wings, engine, propeller/jet, landing gear, tail, cockpit",
        VehicleCategory.BOAT: "hull, deck, mast/superstructure, engine, propeller, rudder, anchor",
        VehicleCategory.AGRICULTURAL: "engine, transmission, chassis, wheels/tracks, PTO, hydraulics, cab",
        VehicleCategory.HELICOPTER: "main rotor, tail rotor, engine, transmission, fuselage, landing skids, cockpit",
        VehicleCategory.CONSTRUCTION: "tracks/wheels, chassis, engine, hydraulic system, boom/arm, bucket, cab",
        VehicleCategory.SPACESHIP: "stages, engines, fuel tanks, payload fairing, guidance, heat shield, landing legs",
        VehicleCategory.TANK: "hull, turret, gun, tracks, engine, transmission, suspension",
        VehicleCategory.BICYCLE: "frame, fork, wheels, drivetrain, handlebars, saddle, brakes",
    }
    parts = key_parts[category]
    return (
        f"hyper-realistic macro ASMR assembly timelapse, giant human hands only, "
        f"no miniature people, no small people, no tiny workers, no human figures, no characters, "
        f"precise mechanical assembly logic, 100% disassembled parts to fully assembled model, "
        f"no floating or teleporting parts, parts attach in realistic order and disappear from "
        f"workbench as installed, final step leaves only the fully assembled model on a clean "
        f"workbench, tweezers, mini screwdriver, soft brush, nippers, 85mm lens, shallow depth "
        f"of field, 8K product quality, bright workshop lighting, {model_name.lower()}, scene: Assembly. "
        f"As parts are attached, they logically disappear from the workbench. "
        f"By the final step, the workspace is completely clean, leaving only the fully assembled model. "
        f"Negative Prompt: {VEHICLE_NEGATIVE_BASE}."
    )


def get_categories() -> list[str]:
    return [c.value for c in VehicleCategory]


def get_models_for_category(category: str) -> list[str]:
    return VEHICLE_MODELS.get(VehicleCategory(category), [])


class VehicleSubtype:
    """Legacy compatibility"""
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