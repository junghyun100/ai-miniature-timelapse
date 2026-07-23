from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from prompt_templates import build_first_frame_prompt
from prompt_templates import get_building_template


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_scene_md(project: Dict[str, Any], scene: Dict[str, Any]) -> str:
    template = get_building_template(project.get("building_type", "hanok"))
    start_second = (scene["id"] - 1) * scene["seconds"]
    end_second = scene["id"] * scene["seconds"]
    first_frame_prompt = build_first_frame_prompt(project["topic"], scene["name"])
    return (
        f"# Scene {scene['id']}: {scene['name']}\n\n"
        f"- Topic: {project['topic']}\n"
        f"- Building Type: {project.get('building_type', 'hanok')}\n"
        f"- Duration: {scene['seconds']} seconds\n"
        f"- Timing: {start_second} to {end_second}\n"
        f"- Materials: {template['materials']}\n"
        f"- Camera: {template['camera']}\n"
        f"- Lighting: {template['lighting']}\n"
        f"- Color Palette: {template.get('color_palette', '')}\n"
        f"- First frame image: `scenes/scene_{scene['id']:02d}_first_frame.png`\n"
        f"- Video output: `renders/scene_{scene['id']:02d}.mp4`\n\n"
        f"## First Frame Prompt\n\n{first_frame_prompt}\n\n"
        f"## Video Prompt\n\n{scene['prompt']}\n\n"
        f"## Negative Prompt\n\n{scene['negative_prompt']}\n"
    )


def export_scene_md(project: Dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for scene in project["scenes"]:
        md = build_scene_md(project, scene)
        (output_dir / f"scene_{scene['id']:02d}.md").write_text(md, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export per-scene Google Flow markdown files.")
    parser.add_argument("project_json")
    parser.add_argument("--output-dir", default="output/scenes_md")
    args = parser.parse_args()

    export_scene_md(load_json(args.project_json), Path(args.output_dir))


if __name__ == "__main__":
    main()
