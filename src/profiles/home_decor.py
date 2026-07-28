"""
Home Decor DIY Profile (home_decor.diy)

Per Section 13.8:
- Workflow: SINGLE_CLIP_FROM_MASTER
- Duration: 10s (single clip)
- Korean narration (max 60 chars no spaces)
- 6-stage sequence in single prompt
- Identity: "tactile mixed-media papercraft and craft ASMR style..."
"""

from ..profile_types import (
    InputMode,
    Profile,
    ScenePlan,
    StyleBible,
    WorkflowMode,
    register_profile,
)

# Korean traditional materials for variation
KOREAN_MATERIALS = [
    "hanji (Korean traditional paper)",
    "najeon (mother-of-pearl)",
    "jogakbo (patchwork wrapping cloth)",
    "myeongju-sil (silk thread)",
    "traditional knots (maedeup)",
    "bamboo (daenamu)",
    "discarded pottery shards",
    "yut-nori sticks",
    "cheongsachorong (traditional lantern) motifs",
]

HOME_DECOR_NARRATION_MAX_NON_WHITESPACE = 60


def count_narration_characters(value: str) -> int:
    """Count narration characters using the channel's whitespace-excluded rule."""
    return sum(not character.isspace() for character in value)


def validate_korean_narration(value: str) -> bool:
    """Return whether narration is non-empty and at most 60 non-whitespace chars."""
    if not isinstance(value, str):
        return False
    count = count_narration_characters(value)
    return 1 <= count <= HOME_DECOR_NARRATION_MAX_NON_WHITESPACE


HOME_DECOR_IDENTITY_LOCK = (
    "tactile mixed-media papercraft and craft ASMR style, specifically featuring "
    "3D layered paper-cutting, origami folding, and organic material collage "
    "captured from a clean, top-down perspective. Macro close-up, hands only, "
    "fixed top-down 45-degree angle, steady camera, bright even studio lighting, "
    "shallow depth of field, clean background, pastel and jewel-tone palette, "
    "9:16 vertical, photorealistic 8K"
)


def _make_style_bible(craft_name: str, materials: list[str]) -> StyleBible:
    return StyleBible(
        identity_lock=HOME_DECOR_IDENTITY_LOCK,
        materials={
            "primary": materials + ["paper", "cardstock", "wire", "glue", "scissors"],
            "secondary": ["paint", "glitter", "beads", "fabric scraps"],
            "tools": [
                "scissors",
                "craft knife",
                "cutting mat",
                "ruler",
                "bone folder",
                "tweezers",
                "glue gun",
                "wire cutters",
            ],
        },
        camera={
            "lens": "macro",
            "angle": "top_down",
            "movement": "fixed",
            "distance": "close",
        },
        lighting={
            "key": "bright even studio lighting",
            "fill": "soft diffuser",
            "mood": "soft_even",
            "consistency": "locked",
        },
        color_palette={
            "primary": ["pastel pink", "mint green", "lavender", "peach"],
            "accent": ["gold", "pearl", "jewel tones"],
            "background": "clean white/light gray",
            "tone": "pastel_jewel",
        },
        workspace={
            "surface": "clean craft table",
            "environment": "bright studio",
            "clutter_rule": "minimal",
        },
        hands_rule="hands_only",
        motion_rule="continuous_flow",
        negative_prompt_base="text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, messy background, cluttered desk, harsh shadows, tilted camera, shaky camera, dark lighting, muddy colors",
    )


def _make_scene_video_prompt(
    craft_name: str, korean_narration: str, materials: list[str], final_object: str
) -> str:
    if not validate_korean_narration(korean_narration):
        raise ValueError("korean_narration must contain 1 to 60 non-whitespace characters")
    materials_str = ", ".join(materials)
    return (
        f"Single 10-second continuous clip, not split into multiple scenes. "
        f"[Opening Hook: close-up of discarded materials, Korean female voiceover speaks narration], "
        f"[Introducing Materials: Korean materials introduced — {materials_str}], "
        f"[Building Begins: hands cut paper, bend wire, start folding], "
        f"[Mid-Build Sequence: satisfying origami folding, layering paper petals, wire stem assembly, tactile ASMR sounds], "
        f"[Detail Showcase: adding gloss, arranging petals, precise placement], "
        f"[Final Reveal: zoom out to finished {final_object} on clean desk]. "
        f"tactile mixed-media papercraft and craft ASMR style, specifically featuring "
        f"3D layered paper-cutting, origami folding, and organic material collage "
        f"captured from a clean, top-down perspective. Macro close-up, hands only, "
        f"fixed top-down 45-degree angle, steady camera, bright even studio lighting, "
        f"shallow depth of field, clean background, pastel and jewel-tone palette, "
        f"9:16 vertical, photorealistic 8K. Korean female voiceover narrates continuously "
        f'without pause: "{korean_narration}". No background music. '
        f"Negative Prompt: text, subtitle, caption, watermark, logo, burnt-in text, overlay text, "
        f"bad anatomy, deformed hands, blurry."
    )


# Single scene plan (10s total)
SCENE_PLAN = [
    ScenePlan(
        scene_id=1,
        name="DIY Craft Tutorial",
        start_state="Raw craft materials and tools only on clean table, no finished object visible",
        ordered_actions=[
            "Opening Hook: close-up of materials with narration",
            "Introducing Materials: Korean materials shown",
            "Building Begins: cutting, bending, folding",
            "Mid-Build Sequence: origami, layering, assembly",
            "Detail Showcase: gloss, arrangement, precision",
            "Final Reveal: zoom out to finished craft",
        ],
        end_state="Finished craft revealed on clean desk",
        forbidden_changes=[
            "Camera angle (top-down 45° fixed)",
            "Lighting (bright even studio)",
            "Background (clean)",
            "Color palette (pastel/jewel)",
            "Hands only rule",
        ],
        input_mode=InputMode.MASTER_IMAGE,
        estimated_clip_duration_seconds=10,
        completion_range="0-100%",
        is_final_scene=True,
        reserved_future_actions=[],
        forbidden_future_actions=[],
        exact_stop_state="Final object reveal on clean desk",
    ),
]


HOME_DECOR_SELECTION_SCHEMA = {
    "type": "object",
    "title": "Home Decor DIY Options",
    "required": ["idea_name", "korean_narration", "materials", "final_object"],
    "properties": {
        "idea_name": {
            "type": "string",
            "title": "Idea name",
            "minLength": 1,
        },
        "korean_narration": {
            "type": "string",
            "title": "Korean narration",
            "minLength": 1,
            "x-length-contract": {
                "max": HOME_DECOR_NARRATION_MAX_NON_WHITESPACE,
                "counting": "non-whitespace-characters",
            },
        },
        "materials": {
            "type": "array",
            "title": "Materials",
            "items": {"type": "string", "minLength": 1},
            "minItems": 1,
        },
        "final_object": {
            "type": "string",
            "title": "Final object",
            "minLength": 1,
        },
    },
    "x-ui-order": ["idea_name", "korean_narration", "materials", "final_object"],
}


home_decor_profile = Profile(
    profile_id="home_decor.diy",
    version="2.0.0",
    topic_label="Home Decor DIY",
    workflow_mode=WorkflowMode.SINGLE_CLIP_FROM_MASTER,
    allowed_total_durations=[10],
    default_total_duration=10,
    clip_duration_seconds=10,
    scene_plans=SCENE_PLAN,
    scene_plans_factory=lambda topic, dur, ctx: SCENE_PLAN,
    selection_schema=HOME_DECOR_SELECTION_SCHEMA,
    style_bible_factory=lambda topic, dur, ctx: make_style_bible(
        ctx["idea_name"], ctx["materials"]
    ),
    first_frame_factory=lambda topic, dur, ctx: (
        {"first_frame_prompt": _make_first_frame_prompt(ctx["idea_name"], ctx["materials"])}
        if ctx.get("scene_id") == 1
        else {}
    ),
    scene_prompt_factory=lambda topic, dur, ctx: {
        "video_prompt": make_scene_video_prompt(
            ctx["idea_name"], ctx["korean_narration"], ctx["materials"], ctx["final_object"]
        )
    },
    audio_contract={
        "type": "korean_narration_plus_asmr",
        "description": "Korean female voiceover (max 60 chars no spaces) + craft ASMR sounds. No background music.",
    },
    negative_prompt_base="text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, messy background, cluttered desk, harsh shadows, tilted camera, shaky camera, dark lighting, muddy colors",
    template_exclusions=["messy background", "dark lighting", "harsh shadows", "tilted camera"],
)

register_profile(home_decor_profile)


def _make_first_frame_prompt(craft_name: str, materials: list[str]) -> str:
    """Generate Master Image prompt for home decor"""
    materials_str = ", ".join(materials)
    return (
        f"Ultra-realistic 8K macro photo of raw craft materials neatly arranged on clean craft table, "
        f"giant human hands only, no miniature people, no small people, no tiny workers, "
        f"no human figures, no characters, no completed craft visible, "
        f"{materials_str}, paper, cardstock, wire, glue, scissors laid out clearly, "
        f"scissors, craft knife, cutting mat, ruler, bone folder, tweezers, glue gun, "
        f"macro lens, shallow depth of field, 8K product photo quality, "
        f"bright even studio lighting, pastel and jewel-tone palette, scene: Master Image."
    )


def make_style_bible(craft_name: str, materials: list[str]) -> StyleBible:
    return _make_style_bible(craft_name, materials)


def make_scene_video_prompt(
    craft_name: str, korean_narration: str, materials: list[str], final_object: str
) -> str:
    return _make_scene_video_prompt(craft_name, korean_narration, materials, final_object)
