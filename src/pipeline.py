from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

from prompt_templates import (
    NEGATIVE_PROMPT,
    STYLE_BLOCK,
    build_common_core,
    build_topic_label,
    get_building_template,
    get_supported_building_types,
)


@dataclass
class Scene:
    id: int
    name: str
    seconds: int
    prompt: str
    negative_prompt: str = NEGATIVE_PROMPT


def build_scene_names(duration: int, building_type: str) -> List[str]:
    template = get_building_template(building_type)
    if duration == 30:
        return template["scene_names_30"]
    return template["scene_names_60"]


def build_scene_prompt(building_type: str, name: str, duration: int) -> str:
    template = get_building_template(building_type)
    base = f"{build_common_core()}, {STYLE_BLOCK}, miniature DIY construction timelapse of a {template['label']}, scene: {name},"
    if duration == 30:
        action = template["scene_prompts_30"][name]
    else:
        action = template["scene_prompts_60"][name]
    return f"{base} {action}."


def add_continuity(building_type: str, scene_name: str, prompt: str, previous_scene: str | None) -> str:
    if not previous_scene:
        return prompt
    continuity = (
        f" Continue directly from the exact final frame of the previous scene '{previous_scene}' without resetting the model, "
        f"treat the previous scene ending as the new starting frame, preserve the same layout, scale, camera angle, and assembled state, "
        f"and keep every visible part physically connected with no jump, no cut, and no scene restart."
    )
    return f"{prompt.rstrip('.')}.{continuity}"


def build_project(
    topic: str,
    duration: int,
    format_: str = "9:16",
    style: str = STYLE_BLOCK,
    variant: str = "",
    building_type: str = "hanok",
) -> dict:
    names = build_scene_names(duration, building_type)
    seconds = duration // len(names)
    scenes = []
    previous_scene = None
    for i, name in enumerate(names):
        prompt = build_scene_prompt(building_type, name, duration)
        prompt = add_continuity(building_type, name, prompt, previous_scene)
        scenes.append(asdict(Scene(id=i + 1, name=name, seconds=seconds, prompt=prompt)))
        previous_scene = name
    return {
        "topic": topic,
        "topic_label": build_topic_label(building_type),
        "building_type": building_type,
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
    parser.add_argument(
        "--building-type",
        default="hanok",
        choices=get_supported_building_types(),
        help="Building template to use for scene structure and prompt wording.",
    )
    parser.add_argument("--duration", type=int, choices=[30, 60], default=60)
    parser.add_argument("--format", dest="format_", choices=["9:16", "16:9"], default="9:16")
    parser.add_argument("--variant", default="")
    parser.add_argument("--output", default="-", help="Output JSON path, or - for stdout")
    args = parser.parse_args()

    project = build_project(args.topic, args.duration, args.format_, STYLE_BLOCK, args.variant, args.building_type)
    payload = json.dumps(project, ensure_ascii=False, indent=2)

    if args.output == "-":
        print(payload)
    else:
        Path(args.output).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
