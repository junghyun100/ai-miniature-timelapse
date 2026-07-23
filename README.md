# ai-miniature-timelapse

Miniature construction timelapse pipeline.

## Use

```bash
python3 src/watch_and_finalize.py "Korean hanok" --duration 60 --base-dir output
```

## What you do

- Render clips from `output/scenes_md/*.md`
- Save them as `output/renders/scene_01.mp4`, `scene_02.mp4`, and so on

## What the pipeline does

- Generates project, prompts, and scene files
- Tracks render status and retry targets
- Stitches automatically when all clips appear

## Details

See `docs/render-checklist.md` for the manual fallback flow.
