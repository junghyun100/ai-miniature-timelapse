from __future__ import annotations

import json
from pathlib import Path


def export_vehicle_data(output_path: Path) -> None:
    """Python vehicle.py 데이터를 JS 소비용 JSON으로 내보냅니다 (직접 하드코딩)."""
    # vehicle.py와 동일 데이터 - 단일 소스
    categories = ["car", "motorcycle", "airplane", "boat", "agricultural", "helicopter", "construction", "spaceship", "tank", "bicycle"]

    models = {
        "car": ["Porsche 911", "Ford Mustang", "Toyota 2000GT", "Ferrari 250 GTO", "Mini Cooper", "Volkswagen Beetle", "BMW 3.0 CSL", "Nissan Skyline GT-R", "Chevrolet Corvette", "Jaguar E-Type"],
        "motorcycle": ["Honda CB750", "Ducati 916", "Harley-Davidson Knucklehead", "Kawasaki Ninja ZX-10R", "BMW R nineT", "Triumph Bonneville", "Yamaha R1", "Moto Guzzi V7", "Indian Chief", "Royal Enfield Interceptor"],
        "airplane": ["Boeing 707", "Supermarine Spitfire", "P-51 Mustang", "F-16 Fighting Falcon", "Cessna 172", "SR-71 Blackbird", "Concorde", "F-22 Raptor", "Mitsubishi Zero", "B-17 Flying Fortress"],
        "boat": ["Chris-Craft Runabout", "America's Cup Yacht", "PT Boat", "U-Boat", "Titanic", "Viking Longship", "Sailing Frigate", "Speedboat", "Submarine", "Hovercraft"],
        "agricultural": ["John Deere 4020", "Ford 8N", "Case IH Magnum", "Fendt 1050", "Massey Ferguson 135", "New Holland T8", "Claas Xerion", "Deutz-Fahr 9340", "Valtra S374", "Kubota M7"],
        "helicopter": ["Bell 47", "UH-1 Huey", "AH-64 Apache", "Mi-24 Hind", "CH-47 Chinook", "Sikorsky S-76", "Robinson R44", "Eurocopter EC135", "Kamov Ka-50", "Boeing CH-47"],
        "construction": ["Caterpillar D11", "Komatsu PC8000", "Liebherr R9800", "Hitachi EX8000", "Volvo EC950", "JCB 3CX", "Case 580", "Doosan DX225", "Hyundai R210", "Sumitomo SH350"],
        "spaceship": ["Saturn V", "Falcon 9", "Space Shuttle", "Starship", "Soyuz", "Delta IV", "Ariane 5", "Atlas V", "Electron", "New Glenn"],
        "tank": ["M1 Abrams", "T-90", "Leopard 2", "Challenger 2", "Type 99", "K2 Black Panther", "Merkava Mk 4", "T-14 Armata", "Panther", "Tiger I"],
        "bicycle": ["Pinarello Dogma", "Specialized S-Works", "Colnago C64", "Bianchi Oltre", "Cervélo R5", "Trek Madone", "Cannondale SuperSix", "Wilier Filante", "Factor Ostro", "Look 795"],
    }

    identityLocks = {
        "car": "One coherent miniature car with unchanged wheelbase, body silhouette, paint color, glass shape, and component layout throughout.",
        "motorcycle": "One coherent miniature motorcycle with unchanged frame geometry, engine position, wheelbase, handlebar shape, and component layout throughout.",
        "airplane": "One coherent miniature airplane with unchanged fuselage length, wingspan, engine configuration, tail design, and landing gear layout throughout.",
        "boat": "One coherent miniature boat with unchanged hull shape, deck layout, superstructure, propulsion type, and component arrangement throughout.",
        "agricultural": "One coherent miniature tractor with unchanged chassis dimensions, engine position, wheel/track configuration, cab shape, and implement mounting points throughout.",
        "helicopter": "One coherent miniature helicopter with unchanged fuselage shape, rotor configuration, tail boom length, engine position, and landing gear type throughout.",
        "construction": "One coherent miniature construction vehicle with unchanged track/wheel configuration, chassis dimensions, hydraulic system layout, boom/arm geometry, and cab position throughout.",
        "spaceship": "One coherent miniature spaceship with unchanged stage configuration, engine cluster arrangement, payload fairing shape, fin/grid fin layout, and overall silhouette throughout.",
        "tank": "One coherent miniature tank with unchanged hull shape, turret geometry, gun barrel length, track type, road wheel arrangement, and component layout throughout.",
        "bicycle": "One coherent miniature bicycle with unchanged frame geometry, wheel size, drivetrain layout, handlebar type, saddle position, and component arrangement throughout.",
    }

    keyParts = {
        "car": "chassis, engine block, transmission, suspension, wheels, body panels, steering, interior components",
        "motorcycle": "engine, frame, wheels, fork, swingarm, tank, exhaust, handlebars, controls",
        "airplane": "fuselage, wings, engine/propeller, landing gear, tail, cockpit, control surfaces",
        "boat": "hull, deck, mast/superstructure, engine, propeller, rudder, anchor, rigging",
        "agricultural": "engine, transmission, chassis, wheels/tracks, PTO, hydraulics, cab, drawbar",
        "helicopter": "main rotor, tail rotor, engine, transmission, fuselage, landing skids, cockpit, swashplate",
        "construction": "tracks/wheels, chassis, engine, hydraulic system, boom/arm, bucket, cab, counterweight",
        "spaceship": "stages, engines, fuel tanks, payload fairing, guidance, heat shield, landing legs, grid fins",
        "tank": "hull, turret, gun, tracks, engine, transmission, suspension, road wheels, optics",
        "bicycle": "frame, fork, wheels, drivetrain, handlebars, saddle, brakes, chain, cranks",
    }

    assemblySteps = {
        "car": [
            "Engine block placed into chassis with precision",
            "Fasteners tightened securing powertrain",
            "Wheels and suspension mounted",
            "Steering rack installed and connected",
            "Body panels fitted seamlessly",
            "Final polish revealing complete model on clean workbench"
        ],
        "motorcycle": [
            "Engine lowered into frame cradle",
            "Bolts torqued securing engine to frame",
            "Wheels and suspension fitted",
            "Fork and handlebars assembled",
            "Tank, seat, and bodywork mounted",
            "Final polish revealing complete bike on clean workbench"
        ],
        "airplane": [
            "Engine mounted to fuselage/wing",
            "Fasteners securing powerplant and mounts",
            "Landing gear retracted and locked",
            "Control surfaces connected and tested",
            "Wings and tail surfaces fitted",
            "Final polish revealing complete aircraft on clean workbench"
        ],
        "boat": [
            "Engine installed in hull",
            "Mounts and fasteners secured",
            "Propeller shaft and rudder connected",
            "Steering and controls linked",
            "Deck, superstructure, and rigging fitted",
            "Final polish revealing complete vessel on clean workbench"
        ],
        "agricultural": [
            "Engine mounted to chassis",
            "Transmission and PTO bolted in place",
            "Wheels/tracks and suspension fitted",
            "Hydraulics and cab installed",
            "Drawbar and implement mounts attached",
            "Final polish revealing complete tractor on clean workbench"
        ],
        "helicopter": [
            "Main transmission and engine installed",
            "Mast and rotor head secured",
            "Tail boom and tail rotor fitted",
            "Landing skids and controls connected",
            "Fuselage panels and cockpit glazed",
            "Final polish revealing complete helicopter on clean workbench"
        ],
        "construction": [
            "Engine and hydraulic pump installed",
            "Tracks/wheels and final drives fitted",
            "Boom and arm structure assembled",
            "Bucket and hydraulic cylinders connected",
            "Cab and counterweight mounted",
            "Final polish revealing complete machine on clean workbench"
        ],
        "spaceship": [
            "Engines mounted to first stage",
            "Stage separation mechanisms secured",
            "Fuel tanks and plumbing installed",
            "Guidance and avionics integrated",
            "Payload fairing and grid fins fitted",
            "Final polish revealing complete rocket on clean workbench"
        ],
        "tank": [
            "Engine and transmission installed in hull",
            "Suspension and road wheels fitted",
            "Tracks connected and tensioned",
            "Turret ring and turret mounted",
            "Gun, optics, and armor fitted",
            "Final polish revealing complete tank on clean workbench"
        ],
        "bicycle": [
            "Bottom bracket and cranks installed",
            "Drivetrain (chain, cassette, derailleurs) fitted",
            "Wheels trued and mounted",
            "Handlebars, stem, and controls assembled",
            "Saddle, seatpost, and brakes installed",
            "Final polish revealing complete bicycle on clean workbench"
        ],
    }

    styleBibles = {
        "car": {
            "materials": {"primary": ["die-cast metal", "plastic", "rubber tires", "clear plastic glass"], "secondary": ["paint", "chrome", "decals"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "file", "cement"]},
            "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
            "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
            "color_palette": {"primary": ["metallic silver", "gunmetal", "chrome"], "accent": ["model-specific paint"], "background": "clean workbench surface", "tone": "cool_cinematic"},
            "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
            "hands_rule": "giant_hands_with_tools",
            "motion_rule": "stop_motion_assembly",
        },
        "motorcycle": {
            "materials": {"primary": ["die-cast metal", "plastic", "rubber tires", "chrome"], "secondary": ["paint", "decals", "leather seat"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "torque wrench"]},
            "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
            "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
            "color_palette": {"primary": ["metallic silver", "chrome", "black"], "accent": ["model-specific paint"], "background": "clean workbench surface", "tone": "cool_cinematic"},
            "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
            "hands_rule": "giant_hands_with_tools",
            "motion_rule": "stop_motion_assembly",
        },
        "airplane": {
            "materials": {"primary": ["die-cast metal", "plastic", "rubber tires"], "secondary": ["paint", "decals", "panel lines"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "pin vise"]},
            "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
            "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
            "color_palette": {"primary": ["metallic silver", "aluminum", "olive drab"], "accent": ["model-specific markings"], "background": "clean workbench surface", "tone": "cool_cinematic"},
            "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
            "hands_rule": "giant_hands_with_tools",
            "motion_rule": "stop_motion_assembly",
        },
        "boat": {
            "materials": {"primary": ["die-cast metal", "plastic", "wood", "fabric sails"], "secondary": ["paint", "varnish", "rigging"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "needle"]},
            "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
            "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
            "color_palette": {"primary": ["white", "navy", "wood tones"], "accent": ["brass", "copper"], "background": "clean workbench surface", "tone": "cool_cinematic"},
            "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
            "hands_rule": "giant_hands_with_tools",
            "motion_rule": "stop_motion_assembly",
        },
        "agricultural": {
            "materials": {"primary": ["die-cast metal", "plastic", "rubber tires/tracks"], "secondary": ["paint", "decals", "hydraulic hoses"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "wrench"]},
            "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
            "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
            "color_palette": {"primary": ["green", "red", "yellow", "blue"], "accent": ["chrome", "black"], "background": "clean workbench surface", "tone": "cool_cinematic"},
            "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
            "hands_rule": "giant_hands_with_tools",
            "motion_rule": "stop_motion_assembly",
        },
        "helicopter": {
            "materials": {"primary": ["die-cast metal", "plastic", "composite rotor blades"], "secondary": ["paint", "decals", "clear canopy"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "pin vise"]},
            "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
            "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
            "color_palette": {"primary": ["olive drab", "gray", "camouflage"], "accent": ["red cross", "warning stripes"], "background": "clean workbench surface", "tone": "cool_cinematic"},
            "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
            "hands_rule": "giant_hands_with_tools",
            "motion_rule": "stop_motion_assembly",
        },
        "construction": {
            "materials": {"primary": ["die-cast metal", "plastic", "rubber tracks/tires"], "secondary": ["paint", "decals", "hydraulic hoses"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "wrench", "allen keys"]},
            "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
            "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
            "color_palette": {"primary": ["yellow", "orange", "gray"], "accent": ["black tracks", "chrome"], "background": "clean workbench surface", "tone": "cool_cinematic"},
            "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
            "hands_rule": "giant_hands_with_tools",
            "motion_rule": "stop_motion_assembly",
        },
        "spaceship": {
            "materials": {"primary": ["die-cast metal", "plastic", "composite"], "secondary": ["paint", "thermal tiles", "decals"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "torque wrench"]},
            "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
            "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
            "color_palette": {"primary": ["white", "black", "metallic"], "accent": ["engine glow", "grid fins"], "background": "clean workbench surface", "tone": "cool_cinematic"},
            "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
            "hands_rule": "giant_hands_with_tools",
            "motion_rule": "stop_motion_assembly",
        },
        "tank": {
            "materials": {"primary": ["die-cast metal", "plastic", "rubber/metal tracks"], "secondary": ["paint", "decals", "photo-etched parts"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "file", "cement"]},
            "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
            "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
            "color_palette": {"primary": ["olive drab", "sand", "gray", "camouflage"], "accent": ["gun metal", "glass"], "background": "clean workbench surface", "tone": "cool_cinematic"},
            "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
            "hands_rule": "giant_hands_with_tools",
            "motion_rule": "stop_motion_assembly",
        },
        "bicycle": {
            "materials": {"primary": ["carbon fiber", "aluminum", "steel", "rubber tires"], "secondary": ["paint", "decals", "bar tape"], "tools": ["tweezers", "mini screwdriver", "soft brush", "nippers", "chain tool", "allen keys"]},
            "camera": {"lens": "85mm", "angle": "macro_closeup", "movement": "fixed", "distance": "macro"},
            "lighting": {"key": "bright workshop overhead", "fill": "soft diffuser", "mood": "bright_clean", "consistency": "locked"},
            "color_palette": {"primary": ["carbon black", "metallic team colors"], "accent": ["chrome", "anodized"], "background": "clean workbench surface", "tone": "cool_cinematic"},
            "workspace": {"surface": "wooden workbench", "environment": "bright workshop", "clutter_rule": "parts_disappear"},
            "hands_rule": "giant_hands_with_tools",
            "motion_rule": "stop_motion_assembly",
        },
    }

    negativeBase = "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry."

    data = {
        "categories": categories,
        "models": models,
        "identityLocks": identityLocks,
        "keyParts": keyParts,
        "assemblySteps": assemblySteps,
        "styleBibles": styleBibles,
        "negativeBase": negativeBase,
    }
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"Exported vehicle data to {output_path}")


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    export_vehicle_data(project_root / "ui" / "data" / "vehicle.json")
