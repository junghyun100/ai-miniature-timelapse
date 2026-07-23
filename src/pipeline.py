from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List


NEGATIVE_PROMPT = "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry"

STYLE_BLOCK = (
    "ultra realistic macro photography, miniature construction site, giant human hands only, "
    "ultra fast timelapse speed, multiple rapid scene cuts, cinematic macro photography, "
    "cinematic studio lighting, shallow depth of field"
)


@dataclass
class Scene:
    id: int
    name: str
    seconds: int
    prompt: str
    negative_prompt: str = NEGATIVE_PROMPT


def build_scene_names(duration: int) -> List[str]:
    if duration == 30:
        return [
            "Foundation and Walls",
            "Roofing and Exterior",
            "Painting, Landscaping, and Reveal",
        ]
    return [
        "Foundation",
        "Wall and Windows",
        "Roofing",
        "Exterior Finishing",
        "Painting and Weathering",
        "Landscaping and Reveal",
    ]


def build_scene_prompt(topic: str, name: str, duration: int) -> str:
    base = f"{STYLE_BLOCK}, miniature DIY construction timelapse of a {topic}, scene: {name},"
    if duration == 30:
        if name == "Foundation and Walls":
            action = "survey the ground, pour miniature foundation, place walls and window frames in one continuous motion"
        elif name == "Roofing and Exterior":
            action = "assemble the roof structure, install roof panels, finish exterior walls, add doors and windows"
        else:
            action = "apply primer and paint, add weathering, place grass and fencing, then reveal the finished building with a cinematic zoom out"
    else:
        mapping = {
            "Foundation": "survey the ground, apply miniature cement, place foundation bricks, and prepare the base",
            "Wall and Windows": "build walls, insert window frames, and align door openings with continuous hand movement",
            "Roofing": "assemble roof framing and install tiles or panels in a smooth timelapse sequence",
            "Exterior Finishing": "finish exterior walls, install doors and windows, and add fine decorative details",
            "Painting and Weathering": "apply primer, paint coats, and weathering effects with realistic tool motion",
            "Landscaping and Reveal": "add grass, soil, fences, and landscaping, then remove the hands and reveal the completed building with a cinematic zoom out",
        }
        action = mapping[name]
    return f"{base} {action}."


def build_project(topic: str, duration: int, format_: str = "9:16", style: str = STYLE_BLOCK, variant: str = "") -> dict:
    names = build_scene_names(duration)
    seconds = duration // len(names)
    scenes = [
        asdict(Scene(id=i + 1, name=name, seconds=seconds, prompt=build_scene_prompt(topic, name, duration)))
        for i, name in enumerate(names)
    ]
    return {
        "topic": topic,
        "duration": duration,
        "format": format_,
        "style": style,
        "variant": variant,
        "scenes": scenes,
        "negative_prompt": NEGATIVE_PROMPT,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a miniature timelapse prompt project.")
    parser.add_argument("topic", help="Target subject, for example 'Korean hanok'.")
    parser.add_argument("--duration", type=int, choices=[30, 60], default=60)
    parser.add_argument("--format", dest="format_", choices=["9:16", "16:9"], default="9:16")
    parser.add_argument("--variant", default="")
    parser.add_argument("--output", default="-", help="Output JSON path, or - for stdout")
    args = parser.parse_args()

    project = build_project(args.topic, args.duration, args.format_, STYLE_BLOCK, args.variant)
    payload = json.dumps(project, ensure_ascii=False, indent=2)

    if args.output == "-":
        print(payload)
    else:
        Path(args.output).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
