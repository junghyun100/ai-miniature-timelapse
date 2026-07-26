from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_ffmpeg_stitch(base_dir: Path, output_path: Path) -> Dict[str, Any]:
    """Original ffmpeg concatenation method."""
    commands_path = base_dir / "exports" / "render-commands.json"
    commands = load_json(commands_path)
    ffmpeg_parts = commands["ffmpeg_concat"].split()
    ffmpeg_parts[1] = str(output_path)
    result = subprocess.run(ffmpeg_parts, capture_output=True, text=True)
    return {
        "command": ffmpeg_parts,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "output": str(output_path),
        "method": "ffmpeg",
    }


def finalize(base_dir: Path, output_path: Path) -> Dict[str, Any]:
    """Run final stitching with ffmpeg."""
    try:
        ffmpeg_result = run_ffmpeg_stitch(base_dir, output_path)
        print(f"✓ ffmpeg stitch succeeded: {output_path}")
        return ffmpeg_result
    except Exception as e:
        return {
            "output": str(output_path),
            "returncode": -1,
            "stdout": "",
            "stderr": f"ffmpeg failed: {e}",
            "method": "failed",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run final stitching (ffmpeg).")
    parser.add_argument("base_dir")
    parser.add_argument("output_path")
    parser.add_argument("--report", default="-")
    args = parser.parse_args()

    report = finalize(Path(args.base_dir), Path(args.output_path))
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report == "-":
        print(payload)
    else:
        Path(args.report).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()