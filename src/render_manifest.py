from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_render_manifest(project: Dict[str, Any]) -> Dict[str, Any]:
    scenes: List[Dict[str, Any]] = []
    for scene in project["scenes"]:
        scenes.append(
            {
                "id": scene["id"],
                "name": scene["name"],
                "duration_seconds": scene["seconds"],
                "prompt": scene["prompt"],
                "negative_prompt": scene["negative_prompt"],
                "input_image": f"scenes/scene_{scene['id']:02d}_first_frame.png",
                "output_video": f"renders/scene_{scene['id']:02d}.mp4",
            }
        )

    return {
        "topic": project["topic"],
        "duration": project["duration"],
        "format": project["format"],
        "style": project["style"],
        "variant": project.get("variant", ""),
        "scenes": scenes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a render manifest for external video generation tools.")
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

