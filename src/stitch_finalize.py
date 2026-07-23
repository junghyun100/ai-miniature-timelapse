from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def finalize(base_dir: Path, output_path: Path) -> Dict[str, Any]:
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
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run final FFmpeg stitching based on render commands.")
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
