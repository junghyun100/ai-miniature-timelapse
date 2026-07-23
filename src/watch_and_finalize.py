from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict

from orchestrator import run as run_orchestrator
from stitch_finalize import finalize as finalize_stitch
from prompt_templates import format_building_type_choices, get_supported_building_types


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def render_files_exist(render_status: Dict[str, Any]) -> bool:
    return not render_status.get("missing_render_files", [])


def main() -> None:
    parser = argparse.ArgumentParser(description="Watch for scene renders and finalize automatically.")
    parser.add_argument("topic", help="Target subject, for example 'Korean hanok'.")
    parser.add_argument("--duration", type=int, choices=[30, 60], default=60)
    parser.add_argument("--building-type", default="hanok", choices=get_supported_building_types())
    parser.add_argument("--list-building-types", action="store_true", help="Print available building templates and exit.")
    parser.add_argument("--format", dest="format_", choices=["9:16", "16:9"], default="9:16")
    parser.add_argument("--variant", default="")
    parser.add_argument("--base-dir", default="output")
    parser.add_argument("--final-output", default="output/exports/final_timeline.mp4")
    parser.add_argument("--poll-seconds", type=int, default=20)
    parser.add_argument("--timeout-seconds", type=int, default=0)
    parser.add_argument("--summary", default="-")
    args = parser.parse_args()

    if args.list_building_types:
        print(format_building_type_choices())
        return

    base_dir = Path(args.base_dir)
    summary = run_orchestrator(args.topic, args.duration, args.format_, args.variant, base_dir, args.building_type)

    start = time.time()
    while True:
        render_status = load_json(base_dir / "exports" / "render-status.json")
        if render_files_exist(render_status):
            stitch_report = finalize_stitch(base_dir, Path(args.final_output))
            break

        if args.timeout_seconds and (time.time() - start) >= args.timeout_seconds:
            stitch_report = {
                "stitched": False,
                "reason": "timeout_waiting_for_renders",
                "final_output": args.final_output,
            }
            break

        time.sleep(args.poll_seconds)

    full_report = {
        "pipeline_summary": summary,
        "render_status": render_status,
        "stitch_report": stitch_report,
    }

    payload = json.dumps(full_report, ensure_ascii=False, indent=2)
    if args.summary == "-":
        print(payload)
    else:
        Path(args.summary).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
