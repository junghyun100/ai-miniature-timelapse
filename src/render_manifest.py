from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_render_manifest(project: dict[str, Any]) -> dict[str, Any]:
    scenes: list[dict[str, Any]] = []
    for scene in project["scenes"]:
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
        scenes.append(
            {
                "id": scene["id"],
                "name": scene["name"],
                "duration_seconds": scene["seconds"],
                "prompt": scene["prompt"],
                "negative_prompt": scene["negative_prompt"],
                "input_mode": input_mode,
                "input_image": input_asset,
                "output_video": f"renders/scene_{scene['id']:02d}.mp4",
                "handoff_image": scene.get(
                    "handoff_asset", f"scenes/scene_{scene['id']:02d}_last_frame.png"
                ),
            }
        )

    return {
        "topic": project["topic"],
        "duration": project["duration"],
        "format": project["format"],
        "style": project["style"],
        "variant": project.get("variant", ""),
        "workflow": "reference_frame_relay",
        "scenes": scenes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a render manifest for external video generation tools."
    )
    parser.add_argument("project_json")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    manifest = build_render_manifest(load_json(args.project_json))
    payload = json.dumps(manifest, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(payload)
    else:
        Path(args.output).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
