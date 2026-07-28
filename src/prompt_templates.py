from __future__ import annotations

NEGATIVE_PROMPT = "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry"

HANDS_ONLY_RULE = (
    "giant human hands only, no miniature people, no small people, no tiny workers, no human figures, "
    "no characters, only hands interacting with the miniature site"
)

CONTINUITY_RULE = (
    "For every scene after Scene 1, upload the exact saved final-frame image from the previous scene as the sole "
    "visual start reference. The opening frame must match that uploaded image before motion begins. Preserve the "
    "same camera, framing, scale, lighting direction, workspace, object placement, installed parts, and loose "
    "materials; do not redesign, reset, rebuild, clean up, or reinterpret the visible state."
)

COMMON_PROMPT_CORE = (
    "You are a top-tier AI video production strategist, master prompt engineer, and viral content creator. "
    "Create a cinematic miniature timelapse workflow that always follows the same structure: topic selection, duration selection, "
    "first-frame image prompt, then continuous motion video prompt. Keep the output text-only and make every scene feel like it was "
    "designed by the same person."
)

COMMON_CONTINUITY_LOCK = (
    "Scene 1 begins from one approved master image showing a completely unstarted subject. "
    "Every later scene uses the exact saved final-frame image from the previous video as its only start image. "
    "Do not introduce a new location, table, tray, composition, floor plan, model, or color scheme. "
    "Keep the camera physically locked until the final reveal. Each scene advances the existing object by one "
    "mechanically plausible step and never reconstructs an earlier step."
)

STYLE_BLOCK = (
    f"ultra realistic macro photography, one fixed miniature-scale build workspace, {HANDS_ONLY_RULE}, "
    "ultra fast procedural timelapse speed in one locked camera composition, cinematic macro photography, "
    f"cinematic studio lighting, shallow depth of field, {CONTINUITY_RULE}"
)

FINAL_FRAME_HANDOFF = (
    "End on a clean, stable, motionless hold for the final 0.5 seconds. Keep every installed part, tool, loose "
    "material, camera parameter, and light direction unchanged so this exact frame can be saved and reused as "
    "the next scene input."
)

FINAL_REVEAL = (
    "After construction is complete, the hands leave the frame. Hold the completed subject, then perform one "
    "subtle cinematic pull-back without changing the subject design."
)


def _first_frame_style(
    label: str,
    surface: str,
    starting_state: str,
    tools: str,
    topic: str,
    scene_name: str,
    lighting: str,
) -> str:
    return (
        f"{label}, {surface}, {HANDS_ONLY_RULE}, {starting_state}, {tools}, "
        f"8K detail, {lighting}, shallow depth of field, {topic}, scene: {scene_name}."
    )


def _standard_scene_action(opening: str, build: str, finish: str) -> str:
    return f"{opening}, {build}, {finish}"


def build_topic_label_from_parts(genre: str, subtype_label: str, detail: str | None = None) -> str:
    label = f"{genre.strip().title()}-{subtype_label.strip()}"
    detail_text = (detail or "").strip()
    return f"{label}-{detail_text}" if detail_text else label


def build_common_core() -> str:
    return f"{COMMON_PROMPT_CORE} {COMMON_CONTINUITY_LOCK}"


def build_identity_lock(building_type: str) -> str:
    key = (building_type or "hanok").strip().lower()
    if key == "hanok":
        return (
            "Identity lock: one coherent single-story Korean hanok with a rectangular timber bay plan, natural "
            "stone footings, warm post-and-beam woodwork, white hanji doors and windows, deep curved black giwa "
            "eaves, and restrained dancheong only on appropriate beam ends and eaves. Never transform it into a "
            "stone castle, Gothic church, European cottage, pagoda tower, palace tower, or fantasy fortress."
        )
    template = get_building_template(key)
    return (
        f"Identity lock: preserve one coherent {template['label']} with the same silhouette, footprint, proportions, "
        f"materials, openings, and color palette through every scene. Never transform it into another subject type, "
        "add an unrequested floor or body section, or replace the established design."
    )


def build_input_frame_contract(scene_id: int) -> str:
    if scene_id == 1:
        return (
            "Start from the uploaded approved master image. The opening frame must match the uploaded image exactly "
            "before the hands begin moving."
        )
    previous_id = scene_id - 1
    return (
        f"Start from the uploaded file scenes/scene_{previous_id:02d}_last_frame.png, the exact saved final frame "
        f"from Scene {previous_id}. Treat it as immutable visual ground truth. The opening frame must match it exactly "
        "before motion begins; do not generate a new first frame."
    )


def build_first_frame_prompt(topic: str, scene_name: str, building_type: str | None = None) -> str:
    key = (building_type or "").strip().lower()
    if key == "hanok":
        return (
            "Ultra realistic macro photography of a completely unstarted miniature Korean hanok construction site, "
            "an untouched compacted-earth tray with an empty rectangular footprint and taut guide strings, every natural "
            "stone footing, timber sill beam, timber column, white hanji frame, rafter, and black giwa roof tile still "
            "separate and neatly staged outside the footprint, no foundation or wall already built, no completed hanok "
            "visible, giant human hands only, no miniature people, no small people, no tiny workers, no human figures, "
            "no characters, giant human fingers beginning the very first action by lifting one natural stone footing "
            "toward its marked position, tiny traditional measuring and woodworking tools, locked 85mm-equivalent macro "
            "camera at a fixed 45-degree angle, 8K detail, soft daylight from camera-left, warm rim light, natural shadows, "
            "cinematic studio lighting, shallow depth of field, one single-story Korean hanok, scene: "
            f"{scene_name}."
        )
    if key == "modern_house":
        return (
            "Ultra realistic macro photography, miniature modern house construction site, clean concrete base slab with "
            "steel guide lines and exposed framing marks, empty window openings, bare foundation footprint, pale dust and "
            "construction grit, giant human hands only, no miniature people, no small people, no tiny workers, no human figures, "
            "no characters, giant human fingers starting the first structural placement, tiny realistic construction tools, "
            "8K detail, clean daylight, cool neutral tones, glossy reflections, cinematic studio lighting, shallow depth of field, "
            "modern house, scene: "
            f"{scene_name}."
        )
    if key == "cafe":
        return (
            "Ultra realistic macro photography, miniature cozy cafe construction site, brick base outline on compacted soil, "
            "storefront footprint marked with thin measuring strings, empty door and window openings, scattered sand and tiny brick chips, "
            "giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, "
            "giant human fingers placing the first cafe foundation pieces, tiny realistic construction tools, 8K detail, golden hour glow, "
            "soft window light, warm interior spill, cinematic bokeh, shallow depth of field, cozy cafe, scene: "
            f"{scene_name}."
        )
    if key == "church":
        return (
            "Ultra realistic macro photography, miniature stone church construction site, chalked foundation outline on dark soil, "
            "first stone blocks and arch markers laid out separately, empty nave footprint, tiny gravel and masonry dust, giant human hands only, "
            "no miniature people, no small people, no tiny workers, no human figures, no characters, giant human fingers placing the first church foundation stones, "
            "tiny realistic masonry tools, 8K detail, high-contrast daylight, stained-glass color spill, dramatic edge light, shallow depth of field, "
            "stone church, scene: "
            f"{scene_name}."
        )
    if key == "castle":
        return (
            "Ultra realistic macro photography, miniature medieval castle construction site, rough soil base with a partially traced fortress outline, "
            "first stone blocks stacked beside an empty keep footprint, timber scaffolding pieces, scattered gravel, giant human hands only, "
            "no miniature people, no small people, no tiny workers, no human figures, no characters, giant human fingers starting the first castle foundation placement, "
            "tiny realistic masonry tools, 8K detail, moody overcast light, hard-edged highlights, atmospheric shadows, shallow depth of field, "
            "medieval castle, scene: "
            f"{scene_name}."
        )
    if key == "temple":
        return (
            "Ultra realistic macro photography, miniature mountain temple construction site, mossy stone base on bare soil, "
            "first pavilion markers and foundation stones arranged separately, empty wooden frame footprint, thin guide lines, tiny lantern parts waiting nearby, "
            "giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, giant human fingers setting the first temple foundation stones, "
            "tiny realistic temple-building tools, 8K detail, misty morning light, soft haze, luminous highlights, tranquil shadows, shallow depth of field, "
            "mountain temple, scene: "
            f"{scene_name}."
        )
    if key == "villa":
        return (
            "Ultra realistic macro photography, miniature luxury villa construction site, clean concrete slab with marble corner markers, "
            "glass frame guides, empty balcony footprint, pale construction dust and aligned measuring strings, giant human hands only, "
            "no miniature people, no small people, no tiny workers, no human figures, no characters, giant human fingers placing the first villa slab pieces, "
            "tiny realistic construction tools, 8K detail, bright premium daylight, polished reflections, soft shadows, luxury showcase lighting, shallow depth of field, "
            "luxury villa, scene: "
            f"{scene_name}."
        )
    if key == "store":
        return (
            "Ultra realistic macro photography, miniature small retail store construction site, brick base outline with storefront width marked by thin strings, "
            "empty glass frame openings, plywood floor markers, scattered tiny sign pieces, giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, "
            "giant human fingers placing the first storefront foundation pieces, tiny realistic construction tools, 8K detail, bright commercial lighting, clean reflections, sign glow, balanced exposure, shallow depth of field, "
            "small retail store, scene: "
            f"{scene_name}."
        )
    if key == "school":
        return (
            "Ultra realistic macro photography, miniature school construction site, brick-red foundation marks on compact soil, "
            "empty classroom wing footprint, chalked guide lines, tiny playground markers, giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, "
            "giant human fingers starting the first school foundation placement, tiny realistic construction tools, 8K detail, soft blue daylight, pale yellow highlights, warm white trim tones, shallow depth of field, "
            "school, scene: "
            f"{scene_name}."
        )
    if key == "hotel":
        return (
            "Ultra realistic macro photography, miniature hotel construction site, polished concrete slab with luxury lobby footprint marked on clean soil, "
            "glass and marble guide pieces laid separately, empty entrance arch opening, giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, "
            "giant human fingers placing the first hotel foundation elements, tiny realistic construction tools, 8K detail, champagne gold daylight, charcoal gray contrast, amber highlights, cinematic studio lighting, shallow depth of field, "
            "hotel, scene: "
            f"{scene_name}."
        )
    if key == "apartment":
        return (
            "Ultra realistic macro photography, miniature apartment building construction site, stacked concrete base with grid-like floor markers, "
            "empty window bay openings, aligned balcony traces, compact soil and fine dust, giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, "
            "giant human fingers placing the first apartment slab pieces, tiny realistic construction tools, 8K detail, light gray daylight, slate blue accents, muted tan shadows, shallow depth of field, "
            "apartment, scene: "
            f"{scene_name}."
        )
    if key == "factory":
        return (
            "Ultra realistic macro photography, miniature factory construction site, industrial concrete floor grid with steel column markers, "
            "empty loading bay outline, pipe guides, safety stripe markers, and raw gravel base, giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, "
            "giant human fingers placing the first factory foundation sections, tiny realistic industrial tools, 8K detail, industrial gray light, safety yellow accents, steel blue reflections, rust orange detail, shallow depth of field, "
            "factory, scene: "
            f"{scene_name}."
        )
    if key == "barn":
        return (
            "Ultra realistic macro photography, miniature barn construction site, weathered dirt base with a simple timber footprint, "
            "empty loft outline, loose hay fibers and rough gravel, first barn post markers separated on the soil, giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, "
            "giant human fingers placing the first barn foundation posts, tiny realistic farm tools, 8K detail, sunset farm light, warm amber highlights, dusty shadows, nostalgic glow, shallow depth of field, "
            "barn, scene: "
            f"{scene_name}."
        )
    if key == "watch":
        return _first_frame_style(
            "Ultra realistic macro product photography",
            "luxury watchmaker bench with a pristine empty surface",
            "no parts assembled yet and watch case and dial parts laid out separately",
            "giant human fingers placing the first precision watch components, tiny realistic watchmaking tools",
            topic,
            scene_name,
            "cinematic studio lighting",
        )
    if key in {"camera", "sneaker", "product"}:
        return _first_frame_style(
            "Ultra realistic macro product photography",
            "premium tabletop product assembly on a pristine empty studio surface",
            "no parts assembled yet and untouched product components arranged separately",
            "giant human fingers placing the first precision components, tiny realistic tools",
            topic,
            scene_name,
            "cinematic studio lighting",
        )
    if key == "home_decor":
        return _first_frame_style(
            "Ultra realistic macro DIY craft photography",
            "pristine empty craft desk with scattered raw materials only",
            "nothing assembled yet and foam, paper, plastic, cloth, twigs, and string laid out separately",
            "giant human fingers arranging the first craft materials, tiny scissors, glue, thread, and brush tools",
            topic,
            scene_name,
            "bright studio lighting",
        )
    if key == "car":
        return (
            "Hyper-realistic macro photo of 100% disassembled miniature car parts neatly arranged on a wooden workbench, "
            "separate chassis, engine block, wheels, suspension, steering rack, body panels, glass pieces, and trim components, "
            "giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, "
            "giant human fingers placing the first car components, tweezers, mini screwdriver, soft brush, 85mm lens, shallow depth of field, "
            "8K product photo quality, bright workshop lighting, automotive assembly, scene: "
            f"{scene_name}."
        )
    if key == "motorcycle":
        return (
            "Hyper-realistic macro photo of 100% disassembled miniature motorcycle parts arranged on a compact metal workbench, "
            "separate frame, fork, fuel tank, engine, wheels, chain, handlebars, and fairing pieces, giant human hands only, no miniature people, "
            "no small people, no tiny workers, no human figures, no characters, giant human fingers aligning the first bike frame pieces, "
            "tweezers, mini screwdriver, soft brush, 85mm lens, shallow depth of field, 8K product photo quality, bright workshop lighting, "
            "motorcycle assembly, scene: "
            f"{scene_name}."
        )
    if key == "airplane":
        return (
            "Hyper-realistic macro photo of 100% disassembled miniature airplane parts neatly arranged on a clean hangar-style workbench, "
            "separate fuselage sections, wings, tail fin, engines, landing gear, cockpit glass, and panel pieces, giant human hands only, "
            "no miniature people, no small people, no tiny workers, no human figures, no characters, giant human fingers placing the first fuselage components, "
            "tweezers, mini screwdriver, soft brush, 85mm lens, shallow depth of field, 8K product photo quality, bright workshop lighting, "
            "airplane assembly, scene: "
            f"{scene_name}."
        )
    if key == "boat":
        return (
            "Hyper-realistic macro photo of 100% disassembled miniature boat parts neatly arranged on a wooden dock-style workbench, "
            "separate hull pieces, deck boards, mast, cabin windows, ropes, rails, and fittings, giant human hands only, no miniature people, "
            "no small people, no tiny workers, no human figures, no characters, giant human fingers arranging the first hull sections, "
            "tweezers, mini screwdriver, soft brush, 85mm lens, shallow depth of field, 8K product photo quality, bright workshop lighting, "
            "boat assembly, scene: "
            f"{scene_name}."
        )
    if key == "helicopter":
        return (
            "Hyper-realistic macro photo of 100% disassembled miniature helicopter parts neatly arranged on a rotorcraft workbench, "
            "separate fuselage shell, main rotor, tail rotor, landing skids, cockpit canopy, engine modules, and panel pieces, giant human hands only, "
            "no miniature people, no small people, no tiny workers, no human figures, no characters, giant human fingers placing the first fuselage modules, "
            "tweezers, mini screwdriver, soft brush, 85mm lens, shallow depth of field, 8K product photo quality, bright workshop lighting, "
            "helicopter assembly, scene: "
            f"{scene_name}."
        )
    if key == "tank":
        return (
            "Hyper-realistic macro photo of 100% disassembled miniature tank parts neatly arranged on a rugged military workbench, "
            "separate hull armor, turret, cannon, track links, suspension, hatches, and exterior plates, giant human hands only, no miniature people, "
            "no small people, no tiny workers, no human figures, no characters, giant human fingers aligning the first armored hull sections, "
            "tweezers, mini screwdriver, soft brush, 85mm lens, shallow depth of field, 8K product photo quality, bright workshop lighting, "
            "tank assembly, scene: "
            f"{scene_name}."
        )
    if key == "bicycle":
        return (
            "Hyper-realistic macro photo of 100% disassembled miniature bicycle parts neatly arranged on a clean bicycle repair bench, "
            "separate frame, wheels, chain, pedals, handlebars, seat, brake cables, and fork pieces, giant human hands only, no miniature people, "
            "no small people, no tiny workers, no human figures, no characters, giant human fingers placing the first frame and wheel parts, "
            "tweezers, mini screwdriver, soft brush, 85mm lens, shallow depth of field, 8K product photo quality, bright workshop lighting, "
            "bicycle assembly, scene: "
            f"{scene_name}."
        )
    if key == "spaceship":
        return (
            "Hyper-realistic macro photo of 100% disassembled miniature spaceship parts neatly arranged on a futuristic assembly bench, "
            "separate hull shells, engine rings, cockpit glass, fins, landing struts, panel modules, and glowing interface parts, giant human hands only, "
            "no miniature people, no small people, no tiny workers, no human figures, no characters, giant human fingers placing the first hull modules, "
            "tweezers, mini screwdriver, soft brush, 85mm lens, shallow depth of field, 8K product photo quality, bright workshop lighting, "
            "spaceship assembly, scene: "
            f"{scene_name}."
        )
    if key in {"construction_vehicle", "agricultural_machinery"}:
        return (
            "Hyper-realistic macro photo of 100% disassembled miniature heavy machine parts neatly arranged on an industrial workbench, "
            "separate chassis, arm or boom sections, wheels or tracks, hydraulic parts, cabin modules, and tool attachments, giant human hands only, "
            "no miniature people, no small people, no tiny workers, no human figures, no characters, giant human fingers placing the first frame modules, "
            "tweezers, mini screwdriver, soft brush, 85mm lens, shallow depth of field, 8K product photo quality, bright workshop lighting, "
            "heavy machine assembly, scene: "
            f"{scene_name}."
        )
    if key in {
        "car",
        "train",
        "airplane",
        "boat",
        "robot",
        "dinosaur",
        "mecha",
        "dragon",
        "wizard_house",
        "spaceship",
        "hoverbike",
        "mech",
    }:
        return _first_frame_style(
            "Hyper-realistic macro photo",
            "100% disassembled miniature model parts neatly arranged on a wooden workbench",
            "no completed model visible and all components separated clearly",
            "giant human hands only, tweezers, mini screwdriver, soft brush, 85mm lens",
            topic,
            scene_name,
            "bright workshop lighting",
        )
    return (
        "Ultra realistic macro photography, miniature construction site, empty sand or soil surface, no materials placed yet, "
        f"{HANDS_ONLY_RULE}, giant human fingers starting the first placement of miniature materials, tiny realistic construction tools, "
        "completely unstarted foundation area, 8K detail, cinematic studio lighting, shallow depth of field, "
        f"{topic}, scene: {scene_name}."
    )


BUILDING_TEMPLATES = {
    "hanok": {
        "label": "traditional Korean hanok",
        "materials": "warm wood, hanji paper windows, curved clay roof tiles, weathered stone foundation",
        "camera": "macro lens, gentle push-ins, slow lateral slides, shallow depth of field",
        "lighting": "soft daylight, warm rim light, natural shadows, cinematic highlights",
        "scene_names_60": [
            "Foundation",
            "Wall and Windows",
            "Roofing",
            "Exterior Finishing",
            "Painting and Weathering",
            "Landscaping and Reveal",
        ],
        "scene_names_30": [
            "Foundation and Walls",
            "Roofing and Exterior",
            "Painting, Landscaping, and Reveal",
        ],
        "scene_prompts_60": {
            "Foundation": (
                "On the untouched compacted-earth footprint, hands tension the guide strings, place natural stone footings "
                "in a precise rectangular bay grid, level each footing, and seat warm timber sill beams; stop with only the "
                "stone-and-sill foundation complete and every column, wall, and roof part still separate"
            ),
            "Wall and Windows": (
                "From the uploaded foundation frame, hands raise warm timber columns into visible mortise-and-tenon joints, "
                "connect lower and upper beams, and insert white hanji door and window frames; stop with a single-story timber "
                "wall frame complete, the original footprint unchanged, and no roof structure present"
            ),
            "Roofing": (
                "From the uploaded timber-frame image, hands place the main crossbeams, purlins, evenly spaced rafters, and "
                "deep curved eave supports, then install black giwa roof tiles row by row; stop with the traditional roof "
                "fully seated and no landscaping, tower, extra wing, or second floor added"
            ),
            "Exterior Finishing": (
                "From the uploaded roofed hanok frame, hands install white hanji doors and windows, finish exposed timber "
                "joinery, add restrained wooden trim, and clean only newly produced debris without moving the building or "
                "changing any opening, roof curve, footprint, camera, or workspace"
            ),
            "Painting and Weathering": (
                "From the uploaded finished shell, hands brush a subtle protective finish over the warm wood and apply "
                "restrained dancheong only to architecturally appropriate beam ends and eaves, preserving white hanji and "
                "black giwa colors; stop before any landscape elements are added"
            ),
            "Landscaping and Reveal": (
                "From the uploaded painted hanok, hands add a stone path, low wall, moss, grass, and one small pine without "
                "moving the building, remove every tool, then leave the frame and reveal the completed hanok"
            ),
        },
        "scene_prompts_30": {
            "Foundation and Walls": (
                "On the completely untouched compacted-earth footprint, hands tension guide strings, place natural stone "
                "footings in a rectangular bay grid, seat timber sill beams, raise warm timber columns with visible "
                "mortise-and-tenon joints, connect the beams, and insert white hanji door and window frames; stop with one "
                "single-story timber wall frame complete, the roof entirely absent, and every unused roof part still staged"
            ),
            "Roofing and Exterior": (
                "Starting from the uploaded exact Scene 1 final frame, hands place crossbeams, purlins, rafters, and deep "
                "curved eave supports, install black giwa tiles row by row, fit white hanji doors and windows, and finish the "
                "exposed timber joinery; stop with the roof and exterior complete and no landscape, tower, second floor, or "
                "new wing added"
            ),
            "Painting, Landscaping, and Reveal": (
                "Starting from the uploaded exact Scene 2 final frame, hands apply a subtle protective wood finish and "
                "restrained dancheong only to correct beam ends and eaves, then add a stone path, low wall, moss, grass, and "
                "one small pine without moving the hanok; remove all tools, let the hands leave, and reveal the finished hanok"
            ),
        },
    },
    "modern_house": {
        "label": "modern house",
        "materials": "smooth concrete, painted drywall, aluminum frames, glass panels, clean trim",
        "camera": "macro lens, crisp straight-on shots, subtle dolly movement, shallow depth of field",
        "lighting": "clean daylight, cool neutral tones, glossy reflections, controlled contrast",
        "scene_names_60": [
            "Foundation",
            "Framing and Windows",
            "Roofing",
            "Exterior Finishing",
            "Painting and Detailing",
            "Landscaping and Reveal",
        ],
        "scene_names_30": [
            "Foundation and Framing",
            "Roofing and Exterior",
            "Painting, Landscaping, and Reveal",
        ],
        "scene_prompts_60": {
            "Foundation": "survey the ground, pour miniature concrete, and set up the foundation slab",
            "Framing and Windows": "build wall framing, insert large window openings, and align the door frame with rapid hand motion",
            "Roofing": "assemble the roof structure and install panels or shingles in a smooth timelapse sequence",
            "Exterior Finishing": "finish the exterior walls, add trim, doors, and window details",
            "Painting and Detailing": "apply primer, paint coats, and subtle surface detailing with realistic tool motion",
            "Landscaping and Reveal": "add grass, soil, fences, and landscaping, then remove the hands and reveal the completed house with a cinematic zoom out",
        },
        "scene_prompts_30": {
            "Foundation and Framing": "survey the ground, pour concrete, and build the wall framing and window openings in one continuous motion",
            "Roofing and Exterior": "assemble the roof structure, install panels, finish exterior walls, and add trim and windows",
            "Painting, Landscaping, and Reveal": "apply paint, add landscaping, then reveal the finished modern house with a cinematic zoom out",
        },
    },
    "cafe": {
        "label": "cozy cafe",
        "materials": "brick facade, wood accents, glass storefront, metal awning, terrace planters",
        "camera": "macro lens, inviting close-ups, gentle tilt shifts, shallow depth of field",
        "lighting": "golden hour glow, soft window light, warm interior spill, cinematic bokeh",
        "scene_names_60": [
            "Foundation",
            "Wall and Windows",
            "Roofing",
            "Exterior Finishing",
            "Painting and Signage",
            "Terrace and Reveal",
        ],
        "scene_names_30": [
            "Foundation and Walls",
            "Roofing and Exterior",
            "Painting, Terrace, and Reveal",
        ],
        "scene_prompts_60": {
            "Foundation": "survey the ground, pour miniature foundation, and prepare the cafe base",
            "Wall and Windows": "build walls, install large storefront windows, and align the door frame",
            "Roofing": "assemble the roof structure and install roof panels in a smooth timelapse sequence",
            "Exterior Finishing": "finish the facade, install doors, windows, and small decorative trims",
            "Painting and Signage": "apply primer, paint coats, and add cafe signage with realistic tool motion",
            "Terrace and Reveal": "add outdoor tables, planters, and terrace details, then remove the hands and reveal the completed cafe with a cinematic zoom out",
        },
        "scene_prompts_30": {
            "Foundation and Walls": "survey the ground, pour the foundation, build walls, and install storefront windows in one continuous motion",
            "Roofing and Exterior": "assemble the roof, finish the facade, and add doors and window trims",
            "Painting, Terrace, and Reveal": "apply paint, add terrace furniture and planters, then reveal the finished cafe with a cinematic zoom out",
        },
    },
    "church": {
        "label": "stone church",
        "materials": "cut stone, stained glass, timber roof beams, iron doors, courtyard stone paving",
        "camera": "macro lens, vertical ascents, dramatic pull-backs, shallow depth of field",
        "lighting": "high-contrast daylight, stained-glass color spill, dramatic edge light",
        "scene_names_60": [
            "Foundation",
            "Nave Walls",
            "Tower and Roof",
            "Exterior Finishing",
            "Stained Glass and Painting",
            "Courtyard and Reveal",
        ],
        "scene_names_30": [
            "Foundation and Walls",
            "Tower and Exterior",
            "Stained Glass, Courtyard, and Reveal",
        ],
        "scene_prompts_60": {
            "Foundation": "survey the ground, pour miniature stone foundation, and prepare the base",
            "Nave Walls": "build tall stone nave walls, arch openings, and doorway framing with continuous hand motion",
            "Tower and Roof": "assemble the tower and roof structure, then install roof panels or shingles in a smooth timelapse sequence",
            "Exterior Finishing": "finish the stone exterior, install doors and architectural details, and refine edges",
            "Stained Glass and Painting": "apply primer, paint coats, and install stained glass details with realistic tool motion",
            "Courtyard and Reveal": "add courtyard stonework, grass, and landscaping, then remove the hands and reveal the completed church with a cinematic zoom out",
        },
        "scene_prompts_30": {
            "Foundation and Walls": "survey the ground, pour the foundation, build the stone walls, and create arch openings in one continuous motion",
            "Tower and Exterior": "assemble the tower and roof, finish the stone exterior, and install the main doors",
            "Stained Glass, Courtyard, and Reveal": "add stained glass, courtyard stonework, and landscaping, then reveal the finished church with a cinematic zoom out",
        },
    },
    "castle": {
        "label": "medieval castle",
        "materials": "rough stone blocks, timber scaffolding, iron gate, slate roofs, weathered battlements",
        "camera": "macro lens, low-angle hero shots, slow crane-like rises, shallow depth of field",
        "lighting": "moody overcast light, hard-edged highlights, atmospheric shadows",
        "scene_names_60": [
            "Foundation",
            "Curtain Walls",
            "Towers and Gate",
            "Roofing and Battlements",
            "Painting and Weathering",
            "Courtyard and Reveal",
        ],
        "scene_names_30": [
            "Foundation and Walls",
            "Towers and Gate",
            "Painting, Courtyard, and Reveal",
        ],
        "scene_prompts_60": {
            "Foundation": "survey the ground, pour miniature stone foundation, and prepare the castle base",
            "Curtain Walls": "build the curtain walls and arches with continuous hand movement",
            "Towers and Gate": "assemble the towers and main gate, then align the entrance details",
            "Roofing and Battlements": "install battlements, roof details, and parapets in a smooth timelapse sequence",
            "Painting and Weathering": "apply primer, paint coats, and weathering effects with realistic tool motion",
            "Courtyard and Reveal": "add courtyard stones, flags, and landscaping, then remove the hands and reveal the completed castle with a cinematic zoom out",
        },
        "scene_prompts_30": {
            "Foundation and Walls": "survey the ground, pour the foundation, build the curtain walls, and set up the arches in one continuous motion",
            "Towers and Gate": "assemble the towers, install the gate, and add battlements and roof details",
            "Painting, Courtyard, and Reveal": "apply paint and weathering, add courtyard stones and flags, then reveal the finished castle with a cinematic zoom out",
        },
    },
    "temple": {
        "label": "mountain temple",
        "materials": "dark wood, painted beams, curved roof tiles, stone steps, lanterns, mossy foundation",
        "camera": "macro lens, serene push-ins, side-to-side reveals, shallow depth of field",
        "lighting": "misty morning light, soft haze, luminous highlights, tranquil shadows",
        "scene_names_60": [
            "Foundation",
            "Pavilion Structure",
            "Roofing",
            "Exterior Finishing",
            "Painting and Details",
            "Garden and Reveal",
        ],
        "scene_names_30": [
            "Foundation and Structure",
            "Roofing and Exterior",
            "Painting, Garden, and Reveal",
        ],
        "scene_prompts_60": {
            "Foundation": "survey the ground, place stone foundation blocks, and prepare the temple base",
            "Pavilion Structure": "build the wooden pavilion frame, columns, and beams with continuous hand motion",
            "Roofing": "assemble the curved temple roof and install layered roof tiles in a smooth timelapse sequence",
            "Exterior Finishing": "finish the wooden exterior, add lanterns and decorative brackets, and refine the details",
            "Painting and Details": "apply primer, paint coats, and ornamental detailing with realistic tool motion",
            "Garden and Reveal": "add moss, stones, trees, and garden details, then remove the hands and reveal the completed temple with a cinematic zoom out",
        },
        "scene_prompts_30": {
            "Foundation and Structure": "survey the ground, place stone foundation blocks, and build the wooden pavilion frame in one continuous motion",
            "Roofing and Exterior": "assemble the curved roof, finish the wooden exterior, and add lanterns and decorative details",
            "Painting, Garden, and Reveal": "apply paint and ornaments, add moss, stones, and trees, then reveal the finished temple with a cinematic zoom out",
        },
    },
    "villa": {
        "label": "luxury villa",
        "materials": "white stucco, marble accents, glass railings, polished stone, landscaped decking",
        "camera": "macro lens, elegant orbit-like slides, clean symmetrical framing, shallow depth of field",
        "lighting": "bright premium daylight, polished reflections, soft shadows, luxury showcase lighting",
        "scene_names_60": [
            "Foundation",
            "Framing and Glass",
            "Roofing",
            "Exterior Finishing",
            "Painting and Detailing",
            "Pool and Reveal",
        ],
        "scene_names_30": [
            "Foundation and Framing",
            "Roofing and Exterior",
            "Painting, Pool, and Reveal",
        ],
        "scene_prompts_60": {
            "Foundation": "survey the ground, pour concrete, and prepare the villa base slab",
            "Framing and Glass": "build the villa frame, install large glass openings, and align balcony structures with rapid hand motion",
            "Roofing": "assemble the roof structure and install sleek panels or tiles in a smooth timelapse sequence",
            "Exterior Finishing": "finish the exterior walls, add marble accents, railings, and refined architectural trims",
            "Painting and Detailing": "apply primer, paint coats, and luxury surface detailing with realistic tool motion",
            "Pool and Reveal": "add pool edges, decking, and landscaping, then remove the hands and reveal the completed villa with a cinematic zoom out",
        },
        "scene_prompts_30": {
            "Foundation and Framing": "survey the ground, pour the slab, build the frame, and install glass openings in one continuous motion",
            "Roofing and Exterior": "assemble the roof, finish the exterior walls, and add railings and marble trim",
            "Painting, Pool, and Reveal": "apply paint, add the pool and landscaping, then reveal the finished villa with a cinematic zoom out",
        },
    },
    "store": {
        "label": "small retail store",
        "materials": "glass storefront, metal frames, plywood, brick base, signage, display shelving",
        "camera": "macro lens, straight product-like shots, subtle pans, shallow depth of field",
        "lighting": "bright commercial lighting, clean reflections, sign glow, balanced exposure",
        "color_palette": "bright whites, warm wood, steel gray, clear glass blues, accent red signage",
        "scene_names_60": [
            "Foundation",
            "Storefront Frame",
            "Roofing",
            "Exterior Finishing",
            "Signage and Display",
            "Street Reveal",
        ],
        "scene_names_30": [
            "Foundation and Frame",
            "Roofing and Exterior",
            "Signage, Display, and Reveal",
        ],
        "scene_prompts_60": {
            "Foundation": "survey the ground, pour the foundation, and prepare the retail store base",
            "Storefront Frame": "build the storefront frame, install large glass windows, and align the entrance with continuous hand motion",
            "Roofing": "assemble the roof structure and install panels in a smooth timelapse sequence",
            "Exterior Finishing": "finish the facade, add brick details, trims, and exterior trim pieces",
            "Signage and Display": "apply primer, paint coats, and add store signage and display details with realistic tool motion",
            "Street Reveal": "add sidewalk, curb, and street details, then remove the hands and reveal the completed store with a cinematic zoom out",
        },
        "scene_prompts_30": {
            "Foundation and Frame": "survey the ground, pour the foundation, build the storefront frame, and install glass windows in one continuous motion",
            "Roofing and Exterior": "assemble the roof, finish the facade, and add brick and trim details",
            "Signage, Display, and Reveal": "apply paint, add signage and displays, then reveal the finished store with a cinematic zoom out",
        },
    },
    "school": {
        "label": "small school building",
        "materials": "brick walls, concrete slabs, classroom windows, painted doors, playground fencing",
        "camera": "macro lens, steady educational tour-like moves, wide-to-close transitions, shallow depth of field",
        "lighting": "clear daylight, soft bounce light, practical shadows, approachable realism",
        "color_palette": "soft blue, pale yellow, brick red, white trim, green playground accents",
        "scene_names_60": [
            "Foundation",
            "Classroom Walls",
            "Roofing",
            "Exterior Finishing",
            "Painting and Signage",
            "Playground and Reveal",
        ],
        "scene_names_30": [
            "Foundation and Walls",
            "Roofing and Exterior",
            "Painting, Playground, and Reveal",
        ],
        "scene_prompts_60": {
            "Foundation": "survey the ground, pour the foundation, and prepare the school base",
            "Classroom Walls": "build classroom walls, place window openings, and align the entry doors with continuous hand motion",
            "Roofing": "assemble the roof structure and install panels in a smooth timelapse sequence",
            "Exterior Finishing": "finish the exterior walls, add doors, windows, and structural trim",
            "Painting and Signage": "apply primer, paint coats, and add school signage with realistic tool motion",
            "Playground and Reveal": "add playground details, fencing, and landscaping, then remove the hands and reveal the completed school with a cinematic zoom out",
        },
        "scene_prompts_30": {
            "Foundation and Walls": "survey the ground, pour the foundation, build classroom walls, and place window openings in one continuous motion",
            "Roofing and Exterior": "assemble the roof, finish the exterior walls, and add doors and window trim",
            "Painting, Playground, and Reveal": "apply paint, add playground details and fencing, then reveal the finished school with a cinematic zoom out",
        },
    },
    "hotel": {
        "label": "boutique hotel",
        "materials": "stone base, glass balconies, curtain walls, polished lobby facade, decorative lights",
        "camera": "macro lens, upscale reveal shots, slow orbit pans, shallow depth of field",
        "lighting": "luxury dusk lighting, warm lobby glow, reflective highlights, cinematic twilight",
        "color_palette": "champagne gold, warm beige, charcoal gray, glass blue, soft amber",
        "scene_names_60": [
            "Foundation",
            "Lobby Frame",
            "Upper Floors",
            "Exterior Finishing",
            "Lighting and Detailing",
            "Night Reveal",
        ],
        "scene_names_30": [
            "Foundation and Lobby",
            "Upper Floors and Exterior",
            "Lighting, Detailing, and Reveal",
        ],
        "scene_prompts_60": {
            "Foundation": "survey the ground, pour the foundation, and prepare the hotel base",
            "Lobby Frame": "build the lobby frame, install tall windows, and align the entrance structure with rapid hand motion",
            "Upper Floors": "assemble the upper floor structure and balcony frames in a smooth timelapse sequence",
            "Exterior Finishing": "finish the exterior facade, add stone trims, balconies, and architectural details",
            "Lighting and Detailing": "apply primer, paint coats, and decorative lighting details with realistic tool motion",
            "Night Reveal": "add plaza paving, ambient lights, and exterior fixtures, then remove the hands and reveal the completed hotel with a cinematic zoom out",
        },
        "scene_prompts_30": {
            "Foundation and Lobby": "survey the ground, pour the foundation, build the lobby frame, and install the entrance windows in one continuous motion",
            "Upper Floors and Exterior": "assemble the upper floors, finish the exterior facade, and add balconies and stone trim",
            "Lighting, Detailing, and Reveal": "apply lighting and detailing, add plaza fixtures, then reveal the finished hotel with a cinematic night-style zoom out",
        },
    },
    "apartment": {
        "label": "apartment building",
        "materials": "concrete slabs, repeating windows, balcony rails, utility panels, clean stucco",
        "camera": "macro lens, vertical stacking shots, repetitive architectural rhythms, shallow depth of field",
        "lighting": "neutral daylight, urban bounce light, crisp shadows, practical realism",
        "color_palette": "light gray, off-white, slate blue, muted tan, dark metal accents",
        "scene_names_60": [
            "Foundation",
            "Floor Stack",
            "Window Grid",
            "Exterior Finishing",
            "Balcony and Detailing",
            "City Reveal",
        ],
        "scene_names_30": [
            "Foundation and Floors",
            "Window Grid and Exterior",
            "Balcony, Detailing, and Reveal",
        ],
        "scene_prompts_60": {
            "Foundation": "survey the ground, pour the foundation, and prepare the apartment base",
            "Floor Stack": "stack the apartment floors and slabs with continuous hand motion",
            "Window Grid": "install repeating window grids and balcony openings in a smooth timelapse sequence",
            "Exterior Finishing": "finish the exterior walls, add panels, trim, and utility details",
            "Balcony and Detailing": "apply primer, paint coats, and balcony detailing with realistic tool motion",
            "City Reveal": "add sidewalks, street edges, and urban landscaping, then remove the hands and reveal the completed apartment building with a cinematic zoom out",
        },
        "scene_prompts_30": {
            "Foundation and Floors": "survey the ground, pour the foundation, and stack the apartment floors in one continuous motion",
            "Window Grid and Exterior": "install the window grids, finish the facade, and add exterior details",
            "Balcony, Detailing, and Reveal": "apply balcony detailing, add urban surroundings, then reveal the finished apartment building with a cinematic zoom out",
        },
    },
    "factory": {
        "label": "industrial factory",
        "materials": "corrugated metal, steel beams, concrete pads, ventilation pipes, warning strips",
        "camera": "macro lens, strong perspective lines, mechanical tracking shots, shallow depth of field",
        "lighting": "cool industrial lighting, overhead fluorescents, hard reflections, gritty contrast",
        "color_palette": "industrial gray, safety yellow, steel blue, rust orange, concrete white",
        "scene_names_60": [
            "Foundation",
            "Steel Frame",
            "Roofing",
            "Exterior Finishing",
            "Pipes and Detailing",
            "Factory Reveal",
        ],
        "scene_names_30": [
            "Foundation and Frame",
            "Roofing and Exterior",
            "Pipes, Detailing, and Reveal",
        ],
        "scene_prompts_60": {
            "Foundation": "survey the ground, pour the foundation, and prepare the factory base",
            "Steel Frame": "assemble the steel frame and support beams with rapid hand motion",
            "Roofing": "install metal roof panels and ventilation structures in a smooth timelapse sequence",
            "Exterior Finishing": "finish the corrugated exterior, doors, and industrial wall details",
            "Pipes and Detailing": "apply primer, paint coats, and add pipes, warning strips, and utility details with realistic tool motion",
            "Factory Reveal": "add loading areas, drive lanes, and industrial yard details, then remove the hands and reveal the completed factory with a cinematic zoom out",
        },
        "scene_prompts_30": {
            "Foundation and Frame": "survey the ground, pour the foundation, and build the steel frame in one continuous motion",
            "Roofing and Exterior": "install the roof panels, finish the exterior, and add doors and industrial details",
            "Pipes, Detailing, and Reveal": "apply industrial detailing, add pipes and yard elements, then reveal the finished factory with a cinematic zoom out",
        },
    },
    "barn": {
        "label": "rustic barn",
        "materials": "weathered timber, red barn siding, stone base, hay loft beams, wooden doors",
        "camera": "macro lens, wide rustic sweeps, gentle push-outs, shallow depth of field",
        "lighting": "sunset farm light, warm amber highlights, dusty shadows, nostalgic glow",
        "color_palette": "barn red, weathered brown, cream trim, hay gold, sunset orange",
        "scene_names_60": [
            "Foundation",
            "Frame and Walls",
            "Roofing",
            "Exterior Finishing",
            "Painting and Weathering",
            "Farmyard and Reveal",
        ],
        "scene_names_30": [
            "Foundation and Frame",
            "Roofing and Exterior",
            "Painting, Farmyard, and Reveal",
        ],
        "scene_prompts_60": {
            "Foundation": "survey the ground, pour the foundation, and prepare the barn base",
            "Frame and Walls": "build the timber frame, walls, and loft structure with continuous hand motion",
            "Roofing": "assemble the roof and install barn panels or shingles in a smooth timelapse sequence",
            "Exterior Finishing": "finish the exterior siding, barn doors, and trim details",
            "Painting and Weathering": "apply primer, paint coats, and rustic weathering with realistic tool motion",
            "Farmyard and Reveal": "add hay bales, fence posts, and farmyard details, then remove the hands and reveal the completed barn with a cinematic zoom out",
        },
        "scene_prompts_30": {
            "Foundation and Frame": "survey the ground, pour the foundation, and build the timber frame and walls in one continuous motion",
            "Roofing and Exterior": "assemble the roof, finish the siding, and add barn doors and trim",
            "Painting, Farmyard, and Reveal": "apply rustic paint and weathering, add hay bales and fence posts, then reveal the finished barn with a cinematic zoom out",
        },
    },
}

GENRE_BY_BUILDING_TYPE = {
    "hanok": "Architecture",
    "modern_house": "Architecture",
    "cafe": "Architecture",
    "church": "Architecture",
    "castle": "Architecture",
    "temple": "Architecture",
    "villa": "Architecture",
    "store": "Architecture",
    "school": "Architecture",
    "hotel": "Architecture",
    "apartment": "Architecture",
    "factory": "Architecture",
    "barn": "Architecture",
    "car": "Vehicle",
    "train": "Vehicle",
    "airplane": "Vehicle",
    "boat": "Vehicle",
    "motorcycle": "Vehicle",
    "agricultural_machinery": "Vehicle",
    "helicopter": "Vehicle",
    "construction_vehicle": "Vehicle",
    "spaceship": "Vehicle",
    "tank": "Vehicle",
    "bicycle": "Vehicle",
    "watch": "Product",
    "camera": "Product",
    "sneaker": "Product",
    "product": "Product",
    "robot": "Character",
    "dinosaur": "Character",
    "mecha": "Character",
    "dragon": "Fantasy",
    "wizard_house": "Fantasy",
    "hoverbike": "SciFi",
    "mech": "SciFi",
    "home_decor": "Home Decor",
}


def get_building_template(building_type: str) -> dict:
    key = building_type.strip().lower()
    return BUILDING_TEMPLATES.get(key, BUILDING_TEMPLATES["hanok"])


def get_genre_for_building_type(building_type: str) -> str:
    key = building_type.strip().lower()
    return GENRE_BY_BUILDING_TYPE.get(key, "Architecture")


def build_topic_label(building_type: str, detail: str | None = None) -> str:
    genre = get_genre_for_building_type(building_type)
    subtype = get_building_template(building_type)["label"]
    return build_topic_label_from_parts(genre, subtype, detail)


def build_topic_detail(building_type: str) -> str:
    template = get_building_template(building_type)
    parts = [
        template.get("color_palette", ""),
        template.get("materials", ""),
        template.get("camera", ""),
        template.get("lighting", ""),
    ]
    compact = " | ".join(part for part in parts if part)
    return compact if compact else template["label"]


def get_supported_building_types() -> list[str]:
    return sorted(BUILDING_TEMPLATES.keys())


def format_building_type_choices() -> str:
    return "\n".join(
        f"- {name}: {BUILDING_TEMPLATES[name]['label']}" for name in get_supported_building_types()
    )


def _generic_template(
    label: str,
    materials: str,
    camera: str,
    lighting: str,
    color_palette: str,
    scene_names_60: list[str],
    scene_names_30: list[str],
    prompts_60: dict,
    prompts_30: dict,
) -> dict:
    return {
        "label": label,
        "materials": materials,
        "camera": camera,
        "lighting": lighting,
        "color_palette": color_palette,
        "scene_names_60": scene_names_60,
        "scene_names_30": scene_names_30,
        "scene_prompts_60": prompts_60,
        "scene_prompts_30": prompts_30,
    }


BUILDING_TEMPLATES.update(
    {
        "home_decor": _generic_template(
            "DIY home decor craft",
            "foam sheets, paper, plastic spoons and bottles, fabric scraps, twigs, thread, glue, ribbon",
            "macro lens, top-down craft-table shots, gentle push-ins, shallow depth of field",
            "bright even studio lighting, clean soft shadows, pastel highlights, jewel-tone accents",
            "pastel pink, sage green, cream, coral, soft gold",
            [
                "Material Prep",
                "Base Shape",
                "Layering",
                "Detailing",
                "Decor Finish",
                "Final Reveal",
            ],
            ["Material Prep and Base", "Layering and Details", "Decor Finish and Reveal"],
            {
                "Material Prep": "arrange the raw materials, separate foam, paper, plastic, cloth, twigs, and thread on a clean craft desk",
                "Base Shape": "cut and shape the base form with continuous hand motion",
                "Layering": "fold, wrap, and layer the craft materials into the main decorative structure",
                "Detailing": "add flowers, ornaments, trims, and texture details with realistic tool motion",
                "Decor Finish": "refine the edges, clean the surface, and add polished decorative accents",
                "Final Reveal": "remove the extra materials, leave only the finished decor piece, and reveal it with a cinematic zoom out",
            },
            {
                "Material Prep and Base": "arrange the raw materials, cut the base shape, and prepare the foundation of the decor piece in one continuous motion",
                "Layering and Details": "wrap, fold, and layer the materials, then add decorative details and accents",
                "Decor Finish and Reveal": "clean the edges, polish the piece, and reveal the finished home decor craft with a cinematic zoom out",
            },
        ),
        "car": _generic_template(
            "miniature car",
            "metal body panels, glass windows, rubber tires, chrome trim, dashboard components",
            "macro lens, low sweeping angles, tight tracking shots, shallow depth of field",
            "studio lighting, glossy reflections, controlled specular highlights",
            "metallic silver, black glass, racing red, chrome highlights",
            [
                "Chassis",
                "Body Frame",
                "Wheels and Suspension",
                "Paint and Trim",
                "Interior Details",
                "Final Reveal",
            ],
            ["Chassis and Frame", "Wheels and Body", "Paint, Interior, and Reveal"],
            {
                "Chassis": "survey the work surface, assemble the chassis frame, and align the wheel mounts with rapid hand motion",
                "Body Frame": "build the car body shell, door frames, and roof structure in a smooth timelapse sequence",
                "Wheels and Suspension": "install wheels, suspension parts, and underbody details with continuous hand movement",
                "Paint and Trim": "apply primer, paint coats, and trim details with realistic tool motion",
                "Interior Details": "add seats, dashboard, steering wheel, and interior finishing details",
                "Final Reveal": "polish the surface, add subtle reflections, then remove the hands and reveal the completed car with a cinematic zoom out",
            },
            {
                "Chassis and Frame": "survey the work surface, assemble the chassis frame, and mount the wheel supports in one continuous motion",
                "Wheels and Body": "install wheels, build the body shell, and align the doors and roofline",
                "Paint, Interior, and Reveal": "apply paint, add interior details, then reveal the finished car with a cinematic zoom out",
            },
        ),
        "train": _generic_template(
            "miniature train",
            "steel rails, metal body, glass windows, connecting couplers, track ballast",
            "macro lens, side-on tracking shots, rhythmic pull-backs, shallow depth of field",
            "bright daylight, metallic reflections, soft industrial bounce",
            "steel gray, deep green, signal red, weathered silver",
            [
                "Engine Base",
                "Passenger Cars",
                "Wheel Assembly",
                "Roof and Trim",
                "Cabin Details",
                "Track Reveal",
            ],
            ["Engine and Cars", "Wheels and Roof", "Details and Reveal"],
            {
                "Engine Base": "survey the work area, place the engine base, and align the frame on the miniature rails",
                "Passenger Cars": "attach passenger cars, windows, and couplers with continuous hand motion",
                "Wheel Assembly": "install wheel assemblies and undercarriage components in a smooth timelapse sequence",
                "Roof and Trim": "finish the roof panels, trim, and exterior rail details with realistic tool motion",
                "Cabin Details": "add cabin seats, control details, and tiny interior finishing touches",
                "Track Reveal": "add track ballast and scenery, then remove the hands and reveal the completed train with a cinematic zoom out",
            },
            {
                "Engine and Cars": "survey the work area, build the engine base, and attach the train cars in one continuous motion",
                "Wheels and Roof": "install wheel assemblies, roof panels, and exterior trim",
                "Details and Reveal": "add cabin details and track scenery, then reveal the finished train with a cinematic zoom out",
            },
        ),
        "airplane": _generic_template(
            "miniature airplane",
            "aluminum fuselage, wing panels, cockpit glass, turbine engines, landing gear",
            "macro lens, dramatic nose-to-tail sweeps, gentle orbit shots, shallow depth of field",
            "clean daylight, sky reflections, bright airline showcase highlights",
            "white fuselage, navy trim, airline blue, chrome silver",
            [
                "Fuselage",
                "Wing Structure",
                "Engines and Gear",
                "Surface Panels",
                "Cabin Details",
                "Runway Reveal",
            ],
            ["Fuselage and Wings", "Engines and Exterior", "Cabin, Panels, and Reveal"],
            {
                "Fuselage": "survey the work surface, assemble the fuselage shell, and align the cockpit section with rapid hand motion",
                "Wing Structure": "attach wing structures and stabilizers in a smooth timelapse sequence",
                "Engines and Gear": "install turbine engines and landing gear with continuous hand movement",
                "Surface Panels": "finish the exterior panels, seams, and rivet details with realistic tool motion",
                "Cabin Details": "add cabin windows, seats, and interior finishing touches",
                "Runway Reveal": "polish the surface, add runway reflections, then remove the hands and reveal the completed airplane with a cinematic zoom out",
            },
            {
                "Fuselage and Wings": "survey the work surface, assemble the fuselage, and attach the wings in one continuous motion",
                "Engines and Exterior": "install engines, landing gear, and exterior panels",
                "Cabin, Panels, and Reveal": "add cabin details, finish the panels, then reveal the finished airplane with a cinematic zoom out",
            },
        ),
        "boat": _generic_template(
            "miniature boat",
            "wood planks, hull resin, deck fittings, ropes, sails or cabin windows",
            "macro lens, gentle waterline sweeps, slow lateral slides, shallow depth of field",
            "sunlit water reflections, warm coastal light, soft highlights",
            "navy blue, teak brown, white sail, seafoam green",
            ["Hull", "Deck Frame", "Sails or Cabin", "Rigging", "Finishing", "Harbor Reveal"],
            ["Hull and Deck", "Rigging and Exterior", "Finishing and Reveal"],
            {
                "Hull": "survey the work surface, shape the hull, and align the keel with continuous hand motion",
                "Deck Frame": "build the deck frame and cabin base in a smooth timelapse sequence",
                "Sails or Cabin": "install the sail masts or cabin windows with realistic tool motion",
                "Rigging": "add ropes, railings, and exterior rigging details",
                "Finishing": "apply primer, paint coats, and weathering details with fine hand motion",
                "Harbor Reveal": "add waterline reflections, dock elements, then remove the hands and reveal the completed boat with a cinematic zoom out",
            },
            {
                "Hull and Deck": "survey the work surface, shape the hull, and build the deck in one continuous motion",
                "Rigging and Exterior": "install masts or cabin details, add rigging, and finish the exterior",
                "Finishing and Reveal": "apply weathering, add dock scenery, then reveal the finished boat with a cinematic zoom out",
            },
        ),
        "watch": _generic_template(
            "luxury watch",
            "polished metal case, glass crystal, dial components, crown, leather or metal strap",
            "macro lens, extreme close-ups, slow orbital slides, shallow depth of field",
            "studio product lighting, polished reflections, crisp highlights",
            "silver, black dial, gold accent, polished steel",
            [
                "Case Body",
                "Dial Assembly",
                "Hands and Crown",
                "Strap Attachment",
                "Polishing",
                "Luxury Reveal",
            ],
            ["Case and Dial", "Hands and Strap", "Polish and Reveal"],
            {
                "Case Body": "survey the work surface, build the watch case, and align the bezel with rapid hand motion",
                "Dial Assembly": "install the dial, markers, and sub-dial details in a smooth timelapse sequence",
                "Hands and Crown": "attach the hands and crown with continuous hand movement",
                "Strap Attachment": "connect the strap or bracelet and refine the side details",
                "Polishing": "polish the surface, clean reflections, and add fine finishing touches",
                "Luxury Reveal": "set the finished watch under clean reflections, then remove the hands and reveal it with a cinematic zoom out",
            },
            {
                "Case and Dial": "survey the work surface, build the case, and install the dial in one continuous motion",
                "Hands and Strap": "attach the hands, crown, and strap or bracelet",
                "Polish and Reveal": "polish the watch and reveal the finished luxury product with a cinematic zoom out",
            },
        ),
        "camera": _generic_template(
            "professional camera",
            "matte black shell, lens glass, metal mounts, chrome buttons, leather grip",
            "macro lens, lens-barrel close-ups, precise sliding moves, shallow depth of field",
            "studio lighting, clean specular highlights, controlled contrast",
            "matte black, chrome silver, red accent, glass blue",
            [
                "Body Shell",
                "Lens Assembly",
                "Controls",
                "Grip and Mount",
                "Polishing",
                "Hero Reveal",
            ],
            ["Body and Lens", "Controls and Grip", "Polish and Reveal"],
            {
                "Body Shell": "survey the work surface, build the camera body shell, and align the mounting points",
                "Lens Assembly": "assemble the lens barrel and glass elements in a smooth timelapse sequence",
                "Controls": "install buttons, dials, and switches with realistic tool motion",
                "Grip and Mount": "attach the grip, strap mount, and side panels with continuous hand movement",
                "Polishing": "polish the surface and refine the finish with precise hand motion",
                "Hero Reveal": "set the camera under studio reflections, then remove the hands and reveal it with a cinematic zoom out",
            },
            {
                "Body and Lens": "survey the work surface, build the body shell, and install the lens assembly in one continuous motion",
                "Controls and Grip": "install controls, grip, and mounting hardware",
                "Polish and Reveal": "polish the camera and reveal the finished product with a cinematic zoom out",
            },
        ),
        "sneaker": _generic_template(
            "sneaker",
            "mesh fabric, rubber sole, stitched panels, lace loops, tongue, foam cushioning",
            "macro lens, low fashion-product angles, dynamic push-ins, shallow depth of field",
            "studio lighting, soft shadow rolls, glossy outsole highlights",
            "white, gum sole, accent color, soft gray",
            [
                "Sole Base",
                "Upper Panels",
                "Lace System",
                "Tongue and Heel",
                "Finishing",
                "Product Reveal",
            ],
            ["Sole and Upper", "Laces and Trim", "Finish and Reveal"],
            {
                "Sole Base": "survey the work surface, shape the sole base, and align the cushioning with rapid hand motion",
                "Upper Panels": "build the upper mesh and stitched panels in a smooth timelapse sequence",
                "Lace System": "install lace loops and lace details with continuous hand movement",
                "Tongue and Heel": "attach the tongue, heel counter, and side branding",
                "Finishing": "apply primer, finish the surface, and clean up the edges with realistic tool motion",
                "Product Reveal": "polish the sneaker under studio light, then remove the hands and reveal it with a cinematic zoom out",
            },
            {
                "Sole and Upper": "survey the work surface, shape the sole, and build the upper in one continuous motion",
                "Laces and Trim": "install the laces, trim, and heel details",
                "Finish and Reveal": "finish the sneaker and reveal the product with a cinematic zoom out",
            },
        ),
        "robot": _generic_template(
            "robot",
            "metal joints, polymer shell, wiring, LED sensors, mechanical limbs",
            "macro lens, low-angle assembly shots, robotic tracking motion, shallow depth of field",
            "cool lab lighting, blue-white glow, sharp metallic highlights",
            "metal gray, neon cyan, soft white, warning orange",
            [
                "Core Frame",
                "Joints and Limbs",
                "Shell Panels",
                "Wiring and Lights",
                "Painting",
                "Robot Reveal",
            ],
            ["Frame and Limbs", "Shell and Lights", "Paint and Reveal"],
            {
                "Core Frame": "survey the work surface, assemble the robot core frame, and align the joint mounts",
                "Joints and Limbs": "attach the joints and limbs in a smooth timelapse sequence",
                "Shell Panels": "install shell panels and armor plates with continuous hand movement",
                "Wiring and Lights": "add wiring, sensors, and LED lights with realistic tool motion",
                "Painting": "apply primer, paint coats, and mechanical surface details",
                "Robot Reveal": "power the robot under cool lab light, then remove the hands and reveal the completed robot with a cinematic zoom out",
            },
            {
                "Frame and Limbs": "survey the work surface, assemble the frame, and attach limbs in one continuous motion",
                "Shell and Lights": "install shell panels and LED lights",
                "Paint and Reveal": "paint the robot and reveal the finished character with a cinematic zoom out",
            },
        ),
        "dinosaur": _generic_template(
            "dinosaur",
            "sculpted skin plates, bone structure, resin base, textured scales, foliage base",
            "macro lens, prehistoric hero angles, slow reveal sweeps, shallow depth of field",
            "warm natural light, earthy shadows, museum-style highlights",
            "earth green, bone ivory, moss brown, amber highlights",
            [
                "Skeleton Base",
                "Body Form",
                "Skin and Tail",
                "Texture Details",
                "Painting",
                "Creature Reveal",
            ],
            ["Body and Tail", "Texture and Reveal", "Finish and Reveal"],
            {
                "Skeleton Base": "survey the work surface, assemble the skeleton base, and align the joints with rapid hand motion",
                "Body Form": "build the body form and limb structure in a smooth timelapse sequence",
                "Skin and Tail": "attach skin plates, tail structure, and back details with continuous hand movement",
                "Texture Details": "add textured scales, claws, and surface details with realistic tool motion",
                "Painting": "apply primer, paint coats, and natural weathering effects",
                "Creature Reveal": "add foliage and ground texture, then remove the hands and reveal the completed dinosaur with a cinematic zoom out",
            },
            {
                "Body and Tail": "survey the work surface, build the body form, and attach the tail in one continuous motion",
                "Texture and Reveal": "apply texture details and reveal the finished creature with a cinematic zoom out",
                "Finish and Reveal": "finish the dinosaur and reveal the completed figure with a cinematic zoom out",
            },
        ),
        "mecha": _generic_template(
            "mecha",
            "armored plates, hydraulic joints, glowing vents, cockpit core, heavy frame",
            "macro lens, dramatic mech hero angles, slow crane-like rises, shallow depth of field",
            "industrial studio lighting, electric rim light, hard metallic highlights",
            "gunmetal, electric blue, hazard orange, silver white",
            [
                "Core Frame",
                "Arms and Legs",
                "Armor Panels",
                "Weapons and Vents",
                "Painting",
                "Mecha Reveal",
            ],
            ["Frame and Limbs", "Armor and Weapons", "Paint and Reveal"],
            {
                "Core Frame": "survey the work surface, assemble the core frame, and align the hydraulic joints with rapid hand motion",
                "Arms and Legs": "attach the arms and legs in a smooth timelapse sequence",
                "Armor Panels": "install armor panels and heavy frame details with continuous hand movement",
                "Weapons and Vents": "add weapons, vents, and mechanical surface details with realistic tool motion",
                "Painting": "apply primer, paint coats, and battle-worn weathering effects",
                "Mecha Reveal": "power the mecha under industrial lights, then remove the hands and reveal the completed mecha with a cinematic zoom out",
            },
            {
                "Frame and Limbs": "survey the work surface, assemble the frame, and attach limbs in one continuous motion",
                "Armor and Weapons": "install armor panels, weapons, and mechanical vents",
                "Paint and Reveal": "paint the mecha and reveal the finished machine with a cinematic zoom out",
            },
        ),
        "dragon": _generic_template(
            "dragon",
            "scaled body plates, wing membranes, horn details, resin base, rock and smoke accents",
            "macro lens, fantasy creature hero shots, slow arc reveals, shallow depth of field",
            "embers and moonlight, dramatic edge light, soft smoke haze",
            "ember red, gold, smoky black, bone ivory",
            [
                "Body Core",
                "Wings and Tail",
                "Horn Details",
                "Texture and Paint",
                "Base and Finish",
                "Dragon Reveal",
            ],
            ["Body and Wings", "Texture and Finish", "Reveal"],
            {
                "Body Core": "survey the work surface, sculpt the dragon body core, and align the limb joints with rapid hand motion",
                "Wings and Tail": "attach the wings and tail structure in a smooth timelapse sequence",
                "Horn Details": "add horn details, claws, and facial features with continuous hand movement",
                "Texture and Paint": "apply primer, paint coats, and scale texture with realistic tool motion",
                "Base and Finish": "add rocks, smoke accents, and base details, then prepare the final surface",
                "Dragon Reveal": "remove the hands and reveal the completed dragon with a cinematic zoom out under ember light",
            },
            {
                "Body and Wings": "survey the work surface, sculpt the body, and attach the wings in one continuous motion",
                "Texture and Finish": "paint the dragon, add texture, and reveal the finished creature with a cinematic zoom out",
                "Reveal": "add finishing accents, then reveal the finished dragon with a cinematic zoom out",
            },
        ),
        "wizard_house": _generic_template(
            "wizard house",
            "timber beams, brass fittings, stone base, glowing windows, rooftop ornaments",
            "macro lens, storybook push-ins, gentle side slides, shallow depth of field",
            "moonlit glow, lantern warmth, magical spill light",
            "deep purple, brass, moonlit blue, warm amber",
            ["Foundation", "Main Structure", "Roof and Windows", "Ornaments", "Coloring", "Reveal"],
            ["Structure and Roof", "Ornaments and Reveal", "Finish and Reveal"],
            {
                "Foundation": "survey the work surface, place the stone foundation, and prepare the magical base with rapid hand motion",
                "Main Structure": "build the timber structure and tower details in a smooth timelapse sequence",
                "Roof and Windows": "install the roof, glowing windows, and structural accents with continuous hand movement",
                "Ornaments": "add brass ornaments, rooftop details, and mystical trims with realistic tool motion",
                "Coloring": "apply primer, paint coats, and magical surface accents",
                "Reveal": "light the windows, then remove the hands and reveal the completed wizard house with a cinematic zoom out",
            },
            {
                "Structure and Roof": "survey the work surface, build the structure, and install the roof in one continuous motion",
                "Ornaments and Reveal": "add ornaments and glowing windows, then reveal the finished wizard house with a cinematic zoom out",
                "Finish and Reveal": "apply magical finishes and reveal the completed house with a cinematic zoom out",
            },
        ),
        "spaceship": _generic_template(
            "spaceship",
            "white hull panels, engine rings, cockpit glass, metallic fins, landing struts",
            "macro lens, sleek fly-through angles, slow orbital slides, shallow depth of field",
            "cool space-studio lighting, neon blue accents, crisp reflections",
            "white, neon blue, graphite gray, chrome silver",
            [
                "Core Hull",
                "Wing Structure",
                "Engines",
                "Surface Panels",
                "Lighting",
                "Launch Reveal",
            ],
            ["Hull and Wings", "Engines and Panels", "Lighting and Reveal"],
            {
                "Core Hull": "survey the work surface, assemble the core hull, and align the cockpit section with rapid hand motion",
                "Wing Structure": "attach wing structures and stabilizers in a smooth timelapse sequence",
                "Engines": "install engine rings and landing struts with continuous hand movement",
                "Surface Panels": "add surface panels, seams, and exterior mechanical details with realistic tool motion",
                "Lighting": "install lighting strips and glow details with fine finishing touches",
                "Launch Reveal": "power the spaceship under cool reflections, then remove the hands and reveal the completed spaceship with a cinematic zoom out",
            },
            {
                "Hull and Wings": "survey the work surface, build the hull, and attach the wings in one continuous motion",
                "Engines and Panels": "install engines, surface panels, and landing struts",
                "Lighting and Reveal": "add lighting details and reveal the finished spaceship with a cinematic zoom out",
            },
        ),
        "hoverbike": _generic_template(
            "hoverbike",
            "compact frame, anti-grav pods, handlebar controls, neon strips, matte body panels",
            "macro lens, dynamic forward sweeps, low hover angles, shallow depth of field",
            "neon studio lighting, electric rim light, polished reflections",
            "black, electric teal, chrome, violet accent",
            ["Frame", "Pods and Wheels", "Body Panels", "Controls", "Lighting", "Street Reveal"],
            ["Frame and Pods", "Panels and Controls", "Lighting and Reveal"],
            {
                "Frame": "survey the work surface, assemble the compact frame, and align the hover mounts with rapid hand motion",
                "Pods and Wheels": "attach anti-grav pods and support components in a smooth timelapse sequence",
                "Body Panels": "install matte body panels and side trims with continuous hand movement",
                "Controls": "add handlebar controls, grips, and switches with realistic tool motion",
                "Lighting": "install neon light strips and glow accents with fine finishing touches",
                "Street Reveal": "power the hoverbike under neon reflections, then remove the hands and reveal the completed hoverbike with a cinematic zoom out",
            },
            {
                "Frame and Pods": "survey the work surface, build the frame, and attach the hover pods in one continuous motion",
                "Panels and Controls": "install body panels, controls, and trim",
                "Lighting and Reveal": "add neon lighting and reveal the finished hoverbike with a cinematic zoom out",
            },
        ),
        "mech": _generic_template(
            "mech",
            "heavy armor plates, piston joints, cockpit shell, hydraulic limbs, weapon mounts",
            "macro lens, towering low-angle shots, slow crane rises, shallow depth of field",
            "industrial lighting, electric blue glow, hard edge reflections",
            "industrial gray, hazard yellow, plasma blue, gunmetal",
            ["Core Frame", "Limbs", "Armor Plates", "Weapons", "Lighting", "Battle Reveal"],
            ["Frame and Limbs", "Armor and Weapons", "Lighting and Reveal"],
            {
                "Core Frame": "survey the work surface, assemble the core frame, and align the hydraulic joints with rapid hand motion",
                "Limbs": "attach the arms and legs in a smooth timelapse sequence",
                "Armor Plates": "install heavy armor plates and cockpit shell panels with continuous hand movement",
                "Weapons": "add weapon mounts and weapon details with realistic tool motion",
                "Lighting": "install cockpit lights and exterior glow accents with fine finishing touches",
                "Battle Reveal": "power the mech under industrial light, then remove the hands and reveal the completed mech with a cinematic zoom out",
            },
            {
                "Frame and Limbs": "survey the work surface, build the frame, and attach limbs in one continuous motion",
                "Armor and Weapons": "install armor plates, weapons, and mechanical trim",
                "Lighting and Reveal": "add lighting accents and reveal the finished mech with a cinematic zoom out",
            },
        ),
    }
)
