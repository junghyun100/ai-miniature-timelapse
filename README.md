# ai-miniature-timelapse

Miniature construction timelapse prompt generator and pipeline scaffold.

## What is included

- A pipeline design document
- A JSON schema for project output
- A Python generator that turns a topic into scene-by-scene prompts
- A text exporter for Google Flow-style prompt bundles
- A render plan generator and QC report template
- A render manifest and local render command generator
- A scene-separated prompt pack and retry plan
- A retry selector that chooses only missing scenes
- An end-to-end orchestrator that writes all artifacts into a single output folder
- A Google Flow manual execution checklist
- Per-scene Markdown exports for Google Flow

## Quick start

Generate a 60-second project:

```bash
python3 src/pipeline.py "Korean hanok" --duration 60 --output project.json
```

Export a readable prompt bundle:

```bash
python3 src/export_prompts.py project.json --output prompts.txt
```

Build a render plan:

```bash
python3 src/render_plan.py project.json --output render-plan.json
```

Build a render manifest:

```bash
python3 src/render_manifest.py project.json --output render-manifest.json
```

Build a prompt pack:

```bash
python3 src/prompt_pack.py project.json --output prompt-pack.json
```

Build a retry plan:

```bash
python3 src/retry_plan.py project.json --output retry-plan.json
```

Select missing scenes for retry:

```bash
python3 src/retry_selector.py output/exports/render-status.json output/qc/retry-plan.json --output retry-selection.json
```

Generate local render commands:

```bash
python3 src/render_commands.py project.json --base-dir output --output render-commands.json
```

Create a QC template:

```bash
python3 src/qc_report.py project.json --output qa-report.json
```

Run the full pipeline:

```bash
python3 src/orchestrator.py "Korean hanok" --duration 60 --base-dir output
```

Export per-scene markdown files:

```bash
python3 src/scene_md_export.py output/input/project.json --output-dir output/scenes_md
```

Finalize stitching:

```bash
python3 src/stitch_finalize.py output output/exports/final_timeline.mp4
```

Manual Google Flow steps:

```bash
cat docs/google-flow-checklist.md
```

## Structure

- `docs/pipeline.md` for the system design
- `docs/google-flow-checklist.md` for manual video generation steps
- `schema/project.schema.json` for the output contract
- `src/pipeline.py` for project generation
- `src/export_prompts.py` for prompt export
- `src/render_plan.py` for stitch/QC planning
- `src/render_manifest.py` for external video generator input
- `src/prompt_pack.py` for first-frame and scene-separated prompts
- `src/render_commands.py` for local execution commands
- `src/retry_plan.py` for scene-only regeneration rules
- `src/retry_selector.py` for selecting missing clips
- `src/scene_md_export.py` for per-scene Markdown exports
- `src/qc_report.py` for quality check scaffolding
- `src/orchestrator.py` for one-shot project generation
- `src/stitch_ffmpeg.sh` for clip concatenation
- `src/stitch_finalize.py` for the final FFmpeg stitch step
- `examples/project.example.json` for a sample project
