from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from prompt_templates import build_first_frame_prompt
from prompt_templates import CONTINUITY_RULE, build_common_core, build_topic_label, get_building_template


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_prompt_pack(project: Dict[str, Any]) -> Dict[str, Any]:
    template = get_building_template(project.get("building_type", "hanok"))
    common_core = build_common_core()
    scenes: List[Dict[str, Any]] = []
    for scene in project["scenes"]:
        prev_scene = project["scenes"][scene["id"] - 2]["name"] if scene["id"] > 1 else ""
        next_scene = project["scenes"][scene["id"]]["name"] if scene["id"] < len(project["scenes"]) else ""
        transition = "continuous carry-over into next scene" if scene["id"] < len(project["scenes"]) else "cinematic reveal and hold"
        first_frame_prompt = build_first_frame_prompt(project["topic"], scene["name"], project.get("building_type", "hanok"))
        continuity_bridge = (
            f"Carry-over: continue directly from the exact final frame of previous scene '{prev_scene}' without resetting the model, "
            f"treat that ending as the new starting frame, preserve the same build progress, camera perspective, and object placement, "
            f"and end by setting up '{next_scene}' with no jump or restart."
            if prev_scene and next_scene
            else CONTINUITY_RULE
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
                "first_frame_prompt": first_frame_prompt,
                "scene_style": {
                    "materials": template["materials"],
                    "camera": template["camera"],
                    "lighting": template["lighting"],
                    "color_palette": template.get("color_palette", ""),
                },
                "google_flow_input": (
                    f"Core: {common_core}\n"
                    f"Scene {scene['id']}\n"
                    f"First Frame Prompt: {first_frame_prompt}\n"
                    f"Start From Previous Final Frame: {prev_scene or 'none'}\n"
                    f"Continuity Rule: {CONTINUITY_RULE}\n"
                    f"Materials: {template['materials']}\n"
                    f"Camera: {template['camera']}\n"
                    f"Lighting: {template['lighting']}\n"
                    f"Color Palette: {template.get('color_palette', '')}\n"
                    f"Bridge: {continuity_bridge}\n"
                    f"Video Prompt: {scene['prompt']}\n"
                    f"Negative Prompt: {scene['negative_prompt']}\n"
                    f"Duration Seconds: {scene['seconds']}\n"
                    f"Transition: {transition}"
                ),
                "video_prompt": scene["prompt"],
                "negative_prompt": scene["negative_prompt"],
                "transition_to_next": transition,
            }
        )

    return {
        "topic": project["topic"],
        "topic_label": project.get("topic_label", build_topic_label(project.get("building_type", "hanok"))),
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
