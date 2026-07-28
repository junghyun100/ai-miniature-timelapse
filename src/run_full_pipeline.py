from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from orchestrator import run as run_orchestrator
from stitch_finalize import finalize as finalize_stitch


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def all_scene_renders_exist(render_status: dict[str, Any]) -> bool:
    return not render_status.get("missing_render_files", [])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the full vehicle assembly pipeline and stitch if renders already exist."
    )
    parser.add_argument("topic", help="Target subject, e.g. 'Porsche 911'.")
    parser.add_argument("--duration", type=int, choices=[30, 60], default=60)
    parser.add_argument("--format", dest="format_", choices=["9:16", "16:9"], default="9:16")
    parser.add_argument("--variant", default="")
    parser.add_argument("--base-dir", default="output")
    parser.add_argument("--final-output", default="output/exports/final_timeline.mp4")
    parser.add_argument("--summary", default="-")
    # Stitching options (passed to OpenMontage VideoStitch)
    parser.add_argument("--transition", choices=["cut", "crossfade", "fade"], default="cut")
    parser.add_argument("--transition-duration", type=float, default=0.5)
    parser.add_argument("--no-normalize", dest="auto_normalize", action="store_false", default=True)
    parser.add_argument("--codec", default="libx264")
    parser.add_argument("--crf", type=int, default=23)
    parser.add_argument("--preset", default="medium")
    parser.add_argument("--dry-run", action="store_true", help="Validate stitch only, don't render")
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    # topic 형식: "vehicle_category:model_name" (예: "car:Porsche 911")
    summary = run_orchestrator(args.topic, args.duration, args.format_, args.variant, base_dir)
    render_status = load_json(base_dir / "exports" / "render-status.json")

    stitch_report: dict[str, Any] = {
        "stitched": False,
        "reason": "missing_render_files",
        "final_output": args.final_output,
    }

    if all_scene_renders_exist(render_status):
        stitch_report = finalize_stitch(
            base_dir,
            Path(args.final_output),
            transition=args.transition,
            transition_duration=args.transition_duration,
            auto_normalize=args.auto_normalize,
            codec=args.codec,
            crf=args.crf,
            preset=args.preset,
            dry_run=args.dry_run,
        )

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
