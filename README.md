# ai-miniature-timelapse

Miniature construction timelapse pipeline.

## Use

1. Generate everything:

```bash
python3 src/watch_and_finalize.py "Korean hanok" --duration 60 --base-dir output
```

2. Render scenes in your video tool using `output/scenes_md/*.md`.
3. Drop finished clips into `output/renders/scene_01.mp4`, `scene_02.mp4`, and so on.
4. The watcher stitches automatically when all clips are present.

## Human Work

- Start the pipeline.
- Create the scene clips in your video tool.
- Save the clips into `output/renders/`.

## Automatic Work

- Project, prompt, and scene file generation
- Retry selection and render status tracking
- Auto-stitching when all clips appear

## Fallback

Use `docs/render-checklist.md` only if you want the manual version of the same flow.
