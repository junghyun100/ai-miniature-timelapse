from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from .domain import Project, compute_source_revision


def _is_project_obj(obj: Any) -> bool:
    return isinstance(obj, Project) or hasattr(obj, "to_dict")


def ensure_source_revision(
    project: Project | dict[str, Any], require_existing: bool = False
) -> str:
    """
    Ensure project has a valid source_revision.
    Computes and attaches revision if missing.
    Raises ValueError if revision is missing and cannot be computed due to corrupt/missing data.
    """
    if isinstance(project, Project):
        if not project.source_revision:
            if not project.profile_id or not project.topic:
                raise ValueError(
                    "Export failed: project missing required fields (profile_id, topic)"
                )
            project.source_revision = project.compute_source_revision()
        rev: str | None = cast(str, project.source_revision)
    else:
        project_dict = cast(dict[str, Any], project)
        rev = cast(str | None, project_dict.get("source_revision"))
        if not rev:
            if require_existing or not project_dict.get("profile_id") or not project_dict.get("topic"):
                raise ValueError(
                    "Export failed: missing source_revision and required project fields (profile_id, topic)"
                )
            try:
                rev = compute_source_revision(project_dict)
                project_dict["source_revision"] = rev
            except Exception as e:
                raise ValueError(
                    f"Export failed: missing source_revision and unable to compute revision: {e}"
                ) from e

    if not rev or not isinstance(rev, str) or not rev.startswith("sha256:"):
        raise ValueError(f"Export failed: invalid or missing source_revision '{rev}'")

    return rev


def load_project(path: str | Path) -> dict[str, Any]:
    """Load project dict from file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    ensure_source_revision(data)
    return data


def export_project_json(
    project: Project | dict[str, Any], current_draft: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Export project as dictionary with attached source_revision.
    Per WP-4 and WP-5: export without valid revision or with stale plan MUST fail.
    """
    if isinstance(project, Project):
        if getattr(project, "is_stale", False):
            raise ValueError("Export failed: plan is stale")
        data = cast(dict[str, Any], project.to_dict())
    else:
        project_dict = cast(dict[str, Any], project)
        if project_dict.get("is_stale"):
            raise ValueError("Export failed: plan is stale")
        data = dict(project_dict)

    rev = ensure_source_revision(data)
    data["source_revision"] = rev

    if current_draft:
        try:
            if compute_source_revision(current_draft) != rev:
                raise ValueError("Export failed: plan is stale (draft revision mismatch)")
        except ValueError:
            raise
        except Exception:
            pass

    return data


def export_text_bundle(
    project: Project | dict[str, Any], current_draft: dict[str, Any] | None = None
) -> str:
    """
    Export human-readable text bundle with source_revision in header.
    Per Section 11.6 and WP-5 Export Parity.
    Uses canonical plan serializer serialize_full_plan when available.
    """
    if isinstance(project, Project):
        if getattr(project, "is_stale", False):
            raise ValueError("Export failed: plan is stale")
        ensure_source_revision(project)
        from .serializers import serialize_full_plan
        return serialize_full_plan(project)

    project_dict = cast(dict[str, Any], project)
    if project_dict.get("is_stale"):
        raise ValueError("Export failed: plan is stale")

    rev = ensure_source_revision(project_dict)

    if current_draft:
        try:
            if compute_source_revision(current_draft) != rev:
                raise ValueError("Export failed: plan is stale (draft revision mismatch)")
        except ValueError:
            raise
        except Exception:
            pass

    topic = project_dict.get("topic", "")
    topic_label = project_dict.get("topic_label", "")
    duration = project_dict.get("duration_seconds") or project_dict.get("duration", 0)
    aspect_ratio = project_dict.get("aspect_ratio") or project_dict.get("format", "")
    profile_id = f"{project_dict.get('profile_id', '')}@{project_dict.get('profile_version', '')}"
    raw_scenes = project_dict.get("scenes", [])
    scenes = []
    for s in raw_scenes:
        scenes.append(
            {
                "id": s.get("id", 1),
                "name": s.get("name", ""),
                "video_prompt": s.get("video_prompt") or s.get("prompt", ""),
                "first_frame_prompt": s.get("first_frame_prompt", ""),
                "negative_prompt": s.get("negative_prompt", ""),
            }
        )

    lines = [
        f"Topic: {topic}",
        f"Topic Label: {topic_label}",
        f"Profile: {profile_id}",
        f"Duration: {duration}s",
        f"Format: {aspect_ratio}",
        f"Source Revision: {rev}",
        "",
    ]
    for scene in scenes:
        lines.append(f"Scene {scene['id']}: {scene['name']}")
        if scene["first_frame_prompt"]:
            lines.append(f"First Frame Prompt: {scene['first_frame_prompt']}")
        lines.append(f"Video Prompt: {scene['video_prompt']}")
        if scene["negative_prompt"]:
            lines.append(f"Negative Prompt: {scene['negative_prompt']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Export prompt bundle or project JSON with source revision."
    )
    parser.add_argument("project_json")
    parser.add_argument("--output", default="-")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    project_data = load_project(args.project_json)

    if args.format == "json":
        exported_data = export_project_json(project_data)
        out_content = json.dumps(exported_data, indent=2, ensure_ascii=False)
    else:
        out_content = export_text_bundle(project_data)

    if args.output == "-":
        print(out_content)
    else:
        Path(args.output).write_text(out_content, encoding="utf-8")


if __name__ == "__main__":
    main()
