# Google Flow Manual Execution Checklist

Use this checklist when you want to run the video generation step manually and keep the rest of the pipeline automated.

## Inputs

- `output/input/project.json`
- `output/input/render-manifest.json`
- `output/input/prompt-pack.json`
- `output/prompts/google-flow-prompts.txt`

## Manual Steps

1. Open `output/input/prompt-pack.json`.
2. Copy the `first_frame_prompt` for scene 1 into your image generator or Google Flow image input.
3. Generate the first frame and save it as `output/scenes/scene_01_first_frame.png`.
4. Copy the matching `video_prompt`, `negative_prompt`, `duration_seconds`, and `transition_to_next` into Google Flow.
5. Generate the video clip and save it as `output/renders/scene_01.mp4`.
6. Repeat for each remaining scene in order.
7. Keep the scene names and duration values exactly as written in the manifest.

## Naming Rules

- First frame images must use: `scene_01_first_frame.png`
- Scene videos must use: `scene_01.mp4`
- Continue the numbering in order for all scenes.
- Scene timing is encoded in `prompt-pack.json` under `timing.start_second` and `timing.end_second`.

## After Rendering

1. Check `output/exports/render-status.json`.
2. If a scene is missing, regenerate only that scene.
3. When all scene clips exist, run FFmpeg stitching.

## Stitch Command

```bash
src/stitch_ffmpeg.sh output/exports/final_timeline.mp4 output/renders/scene_01.mp4 output/renders/scene_02.mp4
```

Replace the example inputs with the full scene list from `output/exports/render-commands.json`.
