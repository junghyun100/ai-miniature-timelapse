from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .prompt_templates import build_first_frame_prompt, get_building_template


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_scene_md(project: dict[str, Any], scene: dict[str, Any]) -> str:
    if project.get("is_stale"):
        raise ValueError("Export failed: plan is stale")

    template = get_building_template(project.get("building_type", "hanok"))
    topic_context = project.get("topic_label") or project["topic"]
    seconds = scene.get("seconds") or scene.get("clip_duration_seconds", 10)
    start_second = (scene["id"] - 1) * seconds
    end_second = scene["id"] * seconds

    first_frame_prompt = scene.get("first_frame_prompt") or ""
    if not first_frame_prompt and scene["id"] == 1:
        first_frame_prompt = build_first_frame_prompt(
            topic_context, scene["name"], project.get("building_type", "hanok")
        )

    video_prompt = scene.get("video_prompt") or scene.get("prompt", "")
    negative_prompt = scene.get("negative_prompt_base") or scene.get("negative_prompt", "")

    input_mode = scene.get(
        "input_mode", "MASTER_IMAGE" if scene["id"] == 1 else "PREVIOUS_FINAL_FRAME"
    )
    input_asset = scene.get(
        "input_asset",
        (
            "scenes/scene_01_master.png"
            if scene["id"] == 1
            else f"scenes/scene_{scene['id'] - 1:02d}_last_frame.png"
        ),
    )
    handoff_asset = scene.get("handoff_asset", f"scenes/scene_{scene['id']:02d}_last_frame.png")
    first_frame_section = (
        f"## Master First Frame Prompt\n\n{first_frame_prompt}\n\n"
        if first_frame_prompt
        else "## Start Image\n\nUse the exact previous scene final-frame image listed above. Do not generate a new first frame.\n\n"
    )
    return (
        f"# Scene {scene['id']}: {scene['name']}\n\n"
        f"- Topic: {project['topic']}\n"
        f"- Topic Label: {project.get('topic_label', '')}\n"
        f"- Building Type: {project.get('building_type', 'hanok')}\n"
        f"- Duration: {seconds} seconds\n"
        f"- Timing: {start_second} to {end_second}\n"
        f"- Materials: {template['materials']}\n"
        f"- Camera: {template['camera']}\n"
        f"- Lighting: {template['lighting']}\n"
        f"- Color Palette: {template.get('color_palette', '')}\n"
        f"- Input mode: `{input_mode}`\n"
        f"- Input image: `{input_asset}`\n"
        f"- Video output: `renders/scene_{scene['id']:02d}.mp4`\n\n"
        f"- Save final frame as: `{handoff_asset}`\n\n"
        f"{first_frame_section}"
        f"## Video Prompt\n\n{video_prompt}\n\n"
        f"## Negative Prompt\n\n{negative_prompt}\n"
    )


def export_scene_md(project: dict[str, Any], output_dir: Path) -> None:
    if project.get("is_stale"):
        raise ValueError("Export failed: plan is stale")
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
