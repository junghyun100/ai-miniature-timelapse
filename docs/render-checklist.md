# Manual Render Checklist

1. Open `output/scenes_md/*.md`.
2. Create the scene clips in your video tool.
3. Save them as `output/renders/scene_01.mp4`, `scene_02.mp4`, and so on.

## When done

- The watcher will auto-stitch when all clips are present.
- If you want to finalize manually, run:

```bash
python3 src/stitch_finalize.py output output/exports/final_timeline.mp4
```
