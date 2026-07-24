from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def load_project(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def export_text_bundle(project: Dict[str, Any]) -> str:
    lines = [
        f"Topic: {project['topic']}",
        f"Topic Label: {project.get('topic_label', '')}",
        f"Duration: {project['duration']}s",
        f"Format: {project['format']}",
        f"Core: {project.get('common_core', '')}",
        f"Negative Prompt: {project.get('negative_prompt', '')}",
        "",
    ]
    for scene in project["scenes"]:
        lines.append(f"Scene {scene['id']}: {scene['name']}")
        lines.append(scene["prompt"])
        lines.append(f"Negative Prompt: {scene['negative_prompt']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Export human-readable prompt bundle from project JSON.")
    parser.add_argument("project_json")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    bundle = export_text_bundle(load_project(args.project_json))
    if args.output == "-":
        print(bundle)
    else:
        Path(args.output).write_text(bundle, encoding="utf-8")


if __name__ == "__main__":
    main()
