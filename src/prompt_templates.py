from __future__ import annotations


NEGATIVE_PROMPT = "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry"

STYLE_BLOCK = (
    "ultra realistic macro photography, miniature construction site, giant human hands only, "
    "ultra fast timelapse speed, multiple rapid scene cuts, cinematic macro photography, "
    "cinematic studio lighting, shallow depth of field"
)


def build_first_frame_prompt(topic: str, scene_name: str) -> str:
    return (
        "Ultra realistic macro photography, miniature construction site, sand or soil surface, "
        "giant human fingers interacting with miniature materials, tiny realistic construction tools, "
        "partially prepared foundation area, 8K detail, cinematic studio lighting, shallow depth of field, "
        f"{topic}, scene: {scene_name}."
    )

