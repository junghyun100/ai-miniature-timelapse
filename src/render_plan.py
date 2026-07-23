from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def load_project(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_render_plan(project: Dict[str, Any]) -> Dict[str, Any]:
    scenes: List[Dict[str, Any]] = []
    for scene in project["scenes"]:
        scenes.append(
            {
                "id": scene["id"],
                "name": scene["name"],
                "duration_seconds": scene["seconds"],
                "input_clip": f"renders/scene_{scene['id']:02d}.mp4",
                "output_clip": f"renders/scene_{scene['id']:02d}_qc.mp4",
            }
        )
    return {
        "topic": project["topic"],
        "duration": project["duration"],
        "format": project["format"],
        "scenes": scenes,
        "stitch_output": "exports/final_timeline.mp4",
        "qa_output": "qc/qa_report.json",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a render plan from a project JSON.")
    parser.add_argument("project_json")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    plan = build_render_plan(load_project(args.project_json))
    payload = json.dumps(plan, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(payload)
    else:
        Path(args.output).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()

