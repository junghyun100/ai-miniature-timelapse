from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_commands(project: Dict[str, Any], base_dir: str = "output") -> Dict[str, Any]:
    scene_videos = [f"{base_dir}/renders/scene_{scene['id']:02d}.mp4" for scene in project["scenes"]]
    return {
        "ffmpeg_concat": f"src/stitch_ffmpeg.sh {base_dir}/exports/final_timeline.mp4 " + " ".join(scene_videos),
        "input_dir": f"{base_dir}/input",
        "prompt_dir": f"{base_dir}/prompts",
        "render_dir": f"{base_dir}/renders",
        "export_dir": f"{base_dir}/exports",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate local render and stitch commands.")
    parser.add_argument("project_json")
    parser.add_argument("--base-dir", default="output")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    commands = build_commands(load_json(args.project_json), args.base_dir)
    payload = json.dumps(commands, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(payload)
    else:
        Path(args.output).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
