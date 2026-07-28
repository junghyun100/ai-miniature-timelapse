from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_retry_selection(
    render_status: dict[str, Any], retry_plan: dict[str, Any]
) -> dict[str, Any]:
    missing_paths = set(render_status.get("missing_render_files", []))
    selected_retries: list[dict[str, Any]] = []

    for item in retry_plan.get("retries", []):
        expected_path = f"output/renders/scene_{item['scene_id']:02d}.mp4"
        if expected_path in missing_paths:
            selected_retries.append(item)

    return {
        "final_exists": render_status.get("final_exists", False),
        "missing_render_files": render_status.get("missing_render_files", []),
        "selected_retries": selected_retries,
        "count": len(selected_retries),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Select retry scenes from render status and retry plan."
    )
    parser.add_argument("render_status_json")
    parser.add_argument("retry_plan_json")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    selection = build_retry_selection(
        load_json(args.render_status_json), load_json(args.retry_plan_json)
    )
    payload = json.dumps(selection, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(payload)
    else:
        Path(args.output).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
