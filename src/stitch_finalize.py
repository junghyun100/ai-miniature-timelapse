from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_ffmpeg_stitch(base_dir: Path, output_path: Path) -> Dict[str, Any]:
    """Original ffmpeg concatenation method."""
    commands_path = base_dir / "exports" / "render-commands.json"
    commands = load_json(commands_path)
    ffmpeg_parts = commands["ffmpeg_concat"].split()
    ffmpeg_parts[1] = str(output_path)
    result = subprocess.run(ffmpeg_parts, capture_output=True, text=True)
    return {
        "command": ffmpeg_parts,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "output": str(output_path),
        "method": "ffmpeg",
    }


def run_remotion_render(base_dir: Path, output_path: Path) -> Dict[str, Any]:
    """New Remotion rendering method."""
    manifest_src = base_dir / "input" / "render-manifest.json"
    remotion_dir = Path(__file__).parent.parent / "remotion-timelapse"
    manifest_dst = remotion_dir / "render_manifest.json"

    if not manifest_src.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_src}")

    if not remotion_dir.exists():
        raise FileNotFoundError(f"Remotion directory not found: {remotion_dir}")

    # Copy manifest to Remotion project
    shutil.copy2(manifest_src, manifest_dst)

    try:
        result = subprocess.run(
            [
                "npx",
                "--prefix",
                str(remotion_dir),
                "remotion",
                "render",
                str(remotion_dir / "src/index.tsx"),
                "timelapse",
                str(output_path),
                f"--config={remotion_dir}/remotion.config.ts",
            ],
            cwd=str(remotion_dir),
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes max
        )

        if result.returncode == 0 and output_path.exists():
            return {
                "output": str(output_path),
                "returncode": 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "method": "remotion",
            }
        else:
            raise subprocess.CalledProcessError(
                result.returncode, "remotion", result.stdout, result.stderr
            )

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        raise RuntimeError(f"Remotion render failed: {e}") from e


def finalize(base_dir: Path, output_path: Path) -> Dict[str, Any]:
    """
    Run final stitching with Remotion as primary, ffmpeg as fallback.
    """
    # Try Remotion first (higher quality, captions, transitions)
    try:
        remotion_result = run_remotion_render(base_dir, output_path)
        print(f"✓ Remotion render succeeded: {output_path}")
        return remotion_result
    except Exception as e:
        print(f"⚠ Remotion render failed: {e}")
        print("  Falling back to ffmpeg...")

    # Fallback: Original ffmpeg concat
    try:
        ffmpeg_result = run_ffmpeg_stitch(base_dir, output_path)
        print(f"✓ ffmpeg stitch succeeded: {output_path}")
        return ffmpeg_result
    except Exception as e:
        return {
            "output": str(output_path),
            "returncode": -1,
            "stdout": "",
            "stderr": f"Both Remotion and ffmpeg failed: {e}",
            "method": "failed",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run final stitching (Remotion preferred, ffmpeg fallback).")
    parser.add_argument("base_dir")
    parser.add_argument("output_path")
    parser.add_argument("--report", default="-")
    args = parser.parse_args()

    report = finalize(Path(args.base_dir), Path(args.output_path))
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report == "-":
        print(payload)
    else:
        Path(args.report).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()