from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_project(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_report(project: dict[str, Any]) -> dict[str, Any]:
    return {
        "topic": project["topic"],
        "duration": project["duration"],
        "checks": [
            {
                "name": "hands_only",
                "status": "pending",
                "note": "Verify only giant human hands appear.",
            },
            {
                "name": "no_mini_people",
                "status": "pending",
                "note": "Verify no miniature people appear.",
            },
            {
                "name": "no_text_watermark",
                "status": "pending",
                "note": "Verify no text, logo, or watermark appears.",
            },
            {
                "name": "scene_continuity",
                "status": "pending",
                "note": "Verify scene endings connect to next scene starts.",
            },
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a basic QC report template.")
    parser.add_argument("project_json")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    report = build_report(load_project(args.project_json))
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(payload)
    else:
        Path(args.output).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
