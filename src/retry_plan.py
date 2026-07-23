from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_retry_plan(project: Dict[str, Any]) -> Dict[str, Any]:
    retries: List[Dict[str, Any]] = []
    for scene in project["scenes"]:
        retries.append(
            {
                "scene_id": scene["id"],
                "scene_name": scene["name"],
                "retry_when": [
                    "hands_missing",
                    "miniature_people_present",
                    "text_or_watermark_present",
                    "scene_continuity_broken",
                    "structure_inconsistent",
                ],
                "action": "regenerate_scene_only",
            }
        )

    return {
        "topic": project["topic"],
        "duration": project["duration"],
        "max_attempts_per_scene": 3,
        "retries": retries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a retry plan for scene regeneration.")
    parser.add_argument("project_json")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    plan = build_retry_plan(load_json(args.project_json))
    payload = json.dumps(plan, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(payload)
    else:
        Path(args.output).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()

