from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict

from export_prompts import export_text_bundle
from pipeline import STYLE_BLOCK, build_project
from qc_report import build_report
from prompt_pack import build_prompt_pack
from render_commands import build_commands
from render_manifest import build_render_manifest
from render_plan import build_render_plan
from retry_selector import build_retry_selection
from retry_plan import build_retry_plan
from prompt_refiner import refine_prompt
from nim_prompt_generator import generate_prompt as generate_nim_prompt
from scene_md_export import export_scene_md
from prompt_templates import format_building_type_choices, get_supported_building_types


def ensure_dirs(base_dir: Path) -> None:
    for rel in ["input", "prompts", "scenes", "renders", "qc", "exports"]:
        (base_dir / rel).mkdir(parents=True, exist_ok=True)


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def collect_render_status(project: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
    scene_status = []
    missing = []
    for scene in project["scenes"]:
        render_path = base_dir / "renders" / f"scene_{scene['id']:02d}.mp4"
        exists = render_path.exists()
        scene_status.append(
            {
                "scene_id": scene["id"],
                "scene_name": scene["name"],
                "render_path": str(render_path),
                "exists": exists,
            }
        )
        if not exists:
            missing.append(str(render_path))

    final_output = base_dir / "exports" / "final_timeline.mp4"
    return {
        "final_output": str(final_output),
        "final_exists": final_output.exists(),
        "scenes": scene_status,
        "missing_render_files": missing,
    }


def run(
    topic: str,
    duration: int,
    format_: str,
    variant: str,
    base_dir: Path,
    building_type: str = "hanok",
    refine_prompts: bool = False,
    use_nim_generate: bool = False,
) -> Dict[str, Any]:
    ensure_dirs(base_dir)
    scene_md_dir = base_dir / "scenes_md"

    project = build_project(topic, duration, format_, STYLE_BLOCK, variant, building_type)
    render_plan = build_render_plan(project)
    render_manifest = build_render_manifest(project)
    prompt_pack = build_prompt_pack(project)
    qc_report = build_report(project)
    retry_plan = build_retry_plan(project)
    prompt_bundle = export_text_bundle(project)

    if use_nim_generate:
        model = os.environ.get("NIM_MODEL", "nvidia/nemotron-3-super-120b-a12b")
        try:
            generated_prompt_bundle = generate_nim_prompt(prompt_bundle, model)
        except RuntimeError as e:
            raise RuntimeError(f"NIM generation failed (required): {e}")
    else:
        generated_prompt_bundle = prompt_bundle
    refined_prompt_bundle = refine_prompt(
        generated_prompt_bundle,
        "Preserve the prompt pack structure, scene continuity, negative prompt, and first-frame-vs-followup-scene distinction."
    ) if refine_prompts else generated_prompt_bundle
    render_commands = build_commands(project, str(base_dir))
    render_status = collect_render_status(project, base_dir)
    retry_selection = build_retry_selection(render_status, retry_plan)

    save_json(base_dir / "input" / "project.json", project)
    save_json(base_dir / "input" / "render-plan.json", render_plan)
    save_json(base_dir / "input" / "render-manifest.json", render_manifest)
    save_json(base_dir / "input" / "prompt-pack.json", prompt_pack)
    save_json(base_dir / "qc" / "retry-plan.json", retry_plan)
    save_json(base_dir / "qc" / "retry-selection.json", retry_selection)
    save_json(base_dir / "exports" / "render-commands.json", render_commands)
    save_json(base_dir / "exports" / "render-status.json", render_status)
    save_json(base_dir / "qc" / "qa-report.json", qc_report)
    final_prompt_bundle = refined_prompt_bundle if refine_prompts else generated_prompt_bundle
    (base_dir / "prompts" / "google-flow-prompts.txt").write_text(final_prompt_bundle, encoding="utf-8")
    export_scene_md(project, scene_md_dir)

    summary = {
        "project_json": str(base_dir / "input" / "project.json"),
        "render_plan_json": str(base_dir / "input" / "render-plan.json"),
        "render_manifest_json": str(base_dir / "input" / "render-manifest.json"),
        "prompt_pack_json": str(base_dir / "input" / "prompt-pack.json"),
        "retry_plan_json": str(base_dir / "qc" / "retry-plan.json"),
        "retry_selection_json": str(base_dir / "qc" / "retry-selection.json"),
        "render_commands_json": str(base_dir / "exports" / "render-commands.json"),
        "render_status_json": str(base_dir / "exports" / "render-status.json"),
        "qc_report_json": str(base_dir / "qc" / "qa-report.json"),
        "prompt_bundle_txt": str(base_dir / "prompts" / "google-flow-prompts.txt"),
        "nim_generation": "enabled" if use_nim_generate else "disabled",
        "prompt_refinement": "enabled" if refine_prompts else "disabled",
        "scene_md_dir": str(scene_md_dir),
        "outputs": [
            "project.json",
            "render-plan.json",
            "render-manifest.json",
            "prompt-pack.json",
            "retry-plan.json",
            "retry-selection.json",
            "render-commands.json",
            "render-status.json",
            "qa-report.json",
            "google-flow-prompts.txt",
            "scenes_md/",
        ],
    }
    save_json(base_dir / "exports" / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full miniature timelapse prompt pipeline.")
    parser.add_argument("topic", help="Target subject, for example 'Korean hanok'.")
    parser.add_argument("--duration", type=int, choices=[30, 60], default=60)
    parser.add_argument("--building-type", default="hanok", choices=get_supported_building_types())
    parser.add_argument("--list-building-types", action="store_true", help="Print available building templates and exit.")
    parser.add_argument("--format", dest="format_", choices=["9:16", "16:9"], default="9:16")
    parser.add_argument("--variant", default="")
    parser.add_argument("--base-dir", default="output", help="Root directory for generated artifacts.")
    parser.add_argument("--use-nim-generate", action="store_true", help="Generate the prompt bundle with NVIDIA NIM when an API key is available.")
    parser.add_argument("--nim-model", default="nvidia/nemotron-3-super-120b-a12b", help="NIM model ID to use (default: nvidia/nemotron-3-super-120b-a12b)")
    parser.add_argument("--refine-prompts", action="store_true", help="Refine the prompt bundle through OpenAI if OPENAI_API_KEY is set.")
    parser.add_argument("--output", default="-", help="Print summary JSON to stdout or write to a file.")
    args = parser.parse_args()

    if args.list_building_types:
        print(format_building_type_choices())
        return

    summary = run(
        args.topic,
        args.duration,
        args.format_,
        args.variant,
        Path(args.base_dir),
        args.building_type,
        args.refine_prompts,
        args.use_nim_generate,
        args.nim_model,
    )
    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(payload)
    else:
        Path(args.output).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
