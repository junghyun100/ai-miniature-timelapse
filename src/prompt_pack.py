from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .prompt_templates import (
    CONTINUITY_RULE,
    build_common_core,
    build_first_frame_prompt,
    build_topic_detail,
    build_topic_label,
    get_building_template,
)


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_prompt_pack(project: dict[str, Any]) -> dict[str, Any]:
    template = get_building_template(project.get("building_type", "hanok"))
    common_core = build_common_core()
    topic_context = project.get("topic_label") or project["topic"]
    scenes: list[dict[str, Any]] = []
    for scene in project["scenes"]:
        prev_scene = project["scenes"][scene["id"] - 2]["name"] if scene["id"] > 1 else ""
        first_frame_prompt = (
            build_first_frame_prompt(
                topic_context, scene["name"], project.get("building_type", "hanok")
            )
            if scene["id"] == 1
            else ""
        )
        input_mode = scene.get(
            "input_mode", "MASTER_IMAGE" if scene["id"] == 1 else "PREVIOUS_FINAL_FRAME"
        )
        input_asset = scene.get(
            "input_asset",
            (
                "scenes/scene_01_master.png"
                if scene["id"] == 1
                else f"scenes/scene_{scene['id'] - 1:02d}_last_frame.png"
            ),
        )
        handoff_asset = scene.get("handoff_asset", f"scenes/scene_{scene['id']:02d}_last_frame.png")
        transition = (
            f"save the exact final frame as {handoff_asset} and use it as the next scene's sole start image"
            if scene["id"] < len(project["scenes"])
            else f"save the final frame as {handoff_asset} for QA and thumbnail use"
        )
        first_frame_line = (
            f"Master First Frame Prompt: {first_frame_prompt}\n" if first_frame_prompt else ""
        )
        scenes.append(
            {
                "id": scene["id"],
                "name": scene["name"],
                "duration_seconds": scene["seconds"],
                "timing": {
                    "start_second": (scene["id"] - 1) * scene["seconds"],
                    "end_second": scene["id"] * scene["seconds"],
                },
                "input_mode": input_mode,
                "input_asset": input_asset,
                "handoff_asset": handoff_asset,
                "first_frame_prompt": first_frame_prompt,
                "first_frame_mode": (
                    "scene_1_only" if scene["id"] == 1 else "previous_final_frame_only"
                ),
                "scene_style": {
                    "materials": template["materials"],
                    "camera": template["camera"],
                    "lighting": template["lighting"],
                    "color_palette": template.get("color_palette", ""),
                },
                "google_flow_input": (
                    f"Core: {common_core}\n"
                    f"Scene {scene['id']}: {scene['name']}\n"
                    f"Input Mode: {input_mode}\n"
                    f"Input Asset: {input_asset}\n"
                    f"{first_frame_line}"
                    f"Previous Scene: {prev_scene or 'none'}\n"
                    f"Continuity Rule: {CONTINUITY_RULE}\n"
                    f"Materials: {template['materials']}\n"
                    f"Camera: {template['camera']}\n"
                    f"Lighting: {template['lighting']}\n"
                    f"Color Palette: {template.get('color_palette', '')}\n"
                    f"Video Prompt: {scene['prompt']}\n"
                    f"Negative Prompt: {scene['negative_prompt']}\n"
                    f"Duration Seconds: {scene['seconds']}\n"
                    f"After Render: {transition}"
                ),
                "video_prompt": scene["prompt"],
                "negative_prompt": scene["negative_prompt"],
                "transition_to_next": transition,
            }
        )

    return {
        "topic": project["topic"],
        "topic_label": project.get(
            "topic_label",
            build_topic_label(
                project.get("building_type", "hanok"),
                build_topic_detail(project.get("building_type", "hanok")),
            ),
        ),
        "topic_detail": project.get(
            "topic_detail", build_topic_detail(project.get("building_type", "hanok"))
        ),
        "building_type": project.get("building_type", "hanok"),
        "duration": project["duration"],
        "format": project["format"],
        "global_style": project["style"],
        "common_core": common_core,
        "global_negative_prompt": project["negative_prompt"],
        "continuity_rule": CONTINUITY_RULE,
        "building_style": {
            "materials": template["materials"],
            "camera": template["camera"],
            "lighting": template["lighting"],
            "color_palette": template.get("color_palette", ""),
        },
        "scenes": scenes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a scene-separated prompt pack.")
    parser.add_argument("project_json")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    pack = build_prompt_pack(load_json(args.project_json))
    payload = json.dumps(pack, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(payload)
    else:
        Path(args.output).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
