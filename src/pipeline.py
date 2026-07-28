from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from prompt_templates import (
    FINAL_FRAME_HANDOFF,
    FINAL_REVEAL,
    NEGATIVE_PROMPT,
    STYLE_BLOCK,
    build_identity_lock,
    build_input_frame_contract,
    build_topic_detail,
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
    input_mode: str
    input_asset: str
    handoff_asset: str
    negative_prompt: str = NEGATIVE_PROMPT


def build_scene_names(duration: int, building_type: str) -> list[str]:
    template = get_building_template(building_type)
    if duration == 30:
        return template["scene_names_30"]
    return template["scene_names_60"]


def build_scene_prompt(
    building_type: str,
    name: str,
    duration: int,
    scene_id: int = 1,
    total_scenes: int = 1,
) -> str:
    template = get_building_template(building_type)
    if duration == 30:
        action = template["scene_prompts_30"][name]
    else:
        action = template["scene_prompts_60"][name]
    end_contract = FINAL_REVEAL if scene_id == total_scenes else FINAL_FRAME_HANDOFF
    return " ".join(
        [
            build_identity_lock(building_type),
            build_input_frame_contract(scene_id),
            STYLE_BLOCK,
            f"Scene {scene_id}, {name}:",
            action.rstrip(".") + ".",
            "All parts move only through visible contact with the giant hands or their tools; no floating, teleporting, "
            "duplicating, or disappearing unattached parts. Installed work remains installed.",
            end_contract,
        ]
    )


def add_continuity(
    building_type: str, scene_name: str, prompt: str, previous_scene: str | None
) -> str:
    if not previous_scene:
        return prompt
    continuity = (
        f" Continue from the uploaded saved final-frame image of '{previous_scene}' as immutable visual ground truth. "
        "Preserve the same layout, scale, camera angle, lighting, assembled state, and loose materials; do not create "
        "a new establishing image or restart the scene."
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
        scene_id = i + 1
        prompt = build_scene_prompt(building_type, name, duration, scene_id, len(names))
        input_mode = "MASTER_IMAGE" if scene_id == 1 else "PREVIOUS_FINAL_FRAME"
        input_asset = (
            "scenes/scene_01_master.png"
            if scene_id == 1
            else f"scenes/scene_{scene_id - 1:02d}_last_frame.png"
        )
        scenes.append(
            asdict(
                Scene(
                    id=scene_id,
                    name=name,
                    seconds=seconds,
                    prompt=prompt,
                    input_mode=input_mode,
                    input_asset=input_asset,
                    handoff_asset=f"scenes/scene_{scene_id:02d}_last_frame.png",
                )
            )
        )
        previous_scene = name
    return {
        "topic": topic,
        "topic_label": build_topic_label(building_type, build_topic_detail(building_type)),
        "topic_detail": build_topic_detail(building_type),
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
    parser.add_argument("--duration", type=int, choices=[30, 60], default=30)
    parser.add_argument("--format", dest="format_", choices=["9:16", "16:9"], default="9:16")
    parser.add_argument("--variant", default="")
    parser.add_argument("--output", default="-", help="Output JSON path, or - for stdout")
    args = parser.parse_args()

    project = build_project(
        args.topic, args.duration, args.format_, STYLE_BLOCK, args.variant, args.building_type
    )
    payload = json.dumps(project, ensure_ascii=False, indent=2)

    if args.output == "-":
        print(payload)
    else:
        Path(args.output).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
