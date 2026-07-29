"""
Persistence Layer - Section 16.2

Persists and restores Project state including:
- Selected profile and subtype
- Source Draft overrides and idea seed
- Duration, format, and Flow execution profile
- Canonical plan and provenance
- Scene branch history and relay state (via RelayBranch)
- Active scene index

Does NOT auto-apply persisted canonical output; returns Project for explicit
"Resume Last Project" action (Section 15.1). Unsupported or corrupt records
are quarantined, not partially merged.

Schema version checking ensures forward/backward compatibility.
"""

from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from .domain import Project

if TYPE_CHECKING:
    from pathlib import Path

# Current schema version that this implementation reads/writes
CURRENT_SCHEMA_VERSION = "2.0"

# Minimum compatible schema version
MIN_COMPATIBLE_SCHEMA_VERSION = "2.0"

# Persistence file names
PROJECT_STATE_FILE = "project_state.json"
QUARANTINE_DIR = "quarantine"


@dataclass
class PersistenceResult:
    """Result of a load/save operation."""

    success: bool
    project: Project | None = None
    error: str | None = None
    quarantined: bool = False
    quarantine_path: str | None = None
    project_id: str | None = None


class PersistenceError(Exception):
    """Raised when persistence operations fail unrecoverably."""


class SchemaVersionError(PersistenceError):
    """Raised when schema version is incompatible."""


class QuarantineError(PersistenceError):
    """Raised when quarantine operation fails."""


def _get_storage_dir(base_dir: Path, project_id: str) -> Path:
    """Get the project-specific storage directory."""
    return base_dir / "projects" / project_id


def _get_project_state_path(base_dir: Path, project_id: str) -> Path:
    """Get the path to the project state JSON file."""
    return _get_storage_dir(base_dir, project_id) / PROJECT_STATE_FILE


def _get_quarantine_dir(base_dir: Path, project_id: str) -> Path:
    """Get the quarantine directory for a project."""
    return _get_storage_dir(base_dir, project_id) / QUARANTINE_DIR


def _quarantine_file(base_dir: Path, project_id: str, source_path: Path, reason: str) -> Path:
    """
    Move a corrupted/incompatible file to quarantine.

    Returns the quarantine path.
    """
    quarantine_dir = _get_quarantine_dir(base_dir, project_id)
    quarantine_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_reason = reason.replace(" ", "_").replace("/", "_")[:50]
    quarantine_name = f"{source_path.stem}_{timestamp}_{safe_reason}{source_path.suffix}"
    quarantine_path = quarantine_dir / quarantine_name

    shutil.move(str(source_path), str(quarantine_path))
    return quarantine_path


def _validate_schema_version(data: dict) -> None:
    """Validate that the schema version is compatible."""
    schema_version = data.get("schema_version", "1.0")  # Default to 1.0 for legacy

    # Check if version is supported
    if schema_version != CURRENT_SCHEMA_VERSION:
        # Allow minor version differences (e.g., 2.0 vs 2.1)
        try:
            current_major = int(CURRENT_SCHEMA_VERSION.split(".")[0])
            data_major = int(schema_version.split(".")[0])
            if current_major != data_major:
                raise SchemaVersionError(
                    f"Major schema version mismatch: expected {CURRENT_SCHEMA_VERSION}, "
                    f"got {schema_version}. Cannot load."
                )
        except (ValueError, IndexError):
            raise SchemaVersionError(f"Invalid schema version format: {schema_version}")


def _validate_required_fields(data: dict) -> list[str]:
    """Validate that required fields are present. Returns list of missing fields."""
    required = [
        "schema_version",
        "profile_id",
        "workflow_mode",
        "topic",
        "topic_label",
        "genre",
        "subtype",
        "duration_seconds",
        "clip_duration_seconds",
        "source_revision",
    ]
    return [field for field in required if field not in data]


def load_project_state(base_dir: Path, project_id: str) -> PersistenceResult:
    """
    Load project state from disk.

    Does NOT auto-apply - returns Project for explicit "Resume Last Project".
    Quarantines corrupted/incompatible records.

    Args:
        base_dir: Base storage directory (e.g., ~/.local/share/ai-miniature-timelapse)
        project_id: Unique project identifier

    Returns:
        PersistenceResult with project (if successful) or error info
    """
    state_path = _get_project_state_path(base_dir, project_id)

    if not state_path.exists():
        return PersistenceResult(success=False, error=f"Project state not found: {project_id}")

    try:
        # Read and parse JSON
        with open(state_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        # Quarantine corrupted file
        quarantine_path = _quarantine_file(
            base_dir, project_id, state_path, f"json_decode_error_{e}"
        )
        return PersistenceResult(
            success=False,
            error=f"Corrupted JSON: {e}",
            quarantined=True,
            quarantine_path=str(quarantine_path),
        )
    except OSError as e:
        return PersistenceResult(success=False, error=f"Failed to read state file: {e}")

    # Validate schema version
    try:
        _validate_schema_version(data)
    except SchemaVersionError as e:
        # Quarantine incompatible schema
        quarantine_path = _quarantine_file(
            base_dir, project_id, state_path, "schema_version_mismatch"
        )
        return PersistenceResult(
            success=False, error=str(e), quarantined=True, quarantine_path=str(quarantine_path)
        )

    # Validate required fields
    missing = _validate_required_fields(data)
    if missing:
        quarantine_path = _quarantine_file(
            base_dir, project_id, state_path, f"missing_fields_{missing[0]}"
        )
        return PersistenceResult(
            success=False,
            error=f"Missing required fields: {missing}",
            quarantined=True,
            quarantine_path=str(quarantine_path),
        )

    # Deserialize Project
    try:
        # Remove metadata fields that aren't part of the project model
        project_data = data.copy()
        project_data.pop("last_saved_at", None)
        project = Project.from_dict(project_data)
    except (KeyError, ValueError, TypeError) as e:
        # Quarantine deserialization failure
        quarantine_path = _quarantine_file(
            base_dir, project_id, state_path, "deserialization_error"
        )
        return PersistenceResult(
            success=False,
            error=f"Deserialization failed: {e}",
            quarantined=True,
            quarantine_path=str(quarantine_path),
        )

    # Validate project invariants
    errors = project.validate()
    if errors:
        # Don't quarantine - just report validation warnings but allow load
        # (user may want to fix and regenerate)
        return PersistenceResult(
            success=True, project=project, error=f"Validation warnings: {'; '.join(errors)}"
        )

    return PersistenceResult(success=True, project=project)


def save_project_state(
    base_dir: Path, project: Project, project_id: str | None = None
) -> PersistenceResult:
    """
    Save project state to disk.

    Generates a project_id if not provided (for new projects).

    Args:
        base_dir: Base storage directory
        project: Project to save
        project_id: Optional existing project ID

    Returns:
        PersistenceResult with success status and project_id
    """
    if project_id is None:
        project_id = str(uuid.uuid4())[:8]

    # Use "projects" subdirectory for organization
    storage_dir = base_dir / "projects" / project_id
    storage_dir.mkdir(parents=True, exist_ok=True)

    state_path = storage_dir / PROJECT_STATE_FILE

    try:
        # Serialize project
        data = project.to_dict()
        data["schema_version"] = CURRENT_SCHEMA_VERSION
        data["last_saved_at"] = datetime.utcnow().isoformat() + "Z"

        # Write atomically (write to temp, then rename)
        temp_path = state_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

        # Atomic rename
        temp_path.replace(state_path)

    except (TypeError, ValueError) as e:
        return PersistenceResult(
            success=False, error=f"Serialization failed: {e}", project_id=project_id
        )
    except OSError as e:
        return PersistenceResult(
            success=False, error=f"Failed to write state file: {e}", project_id=project_id
        )

    return PersistenceResult(success=True, project=project, project_id=project_id)


def delete_project_state(base_dir: Path, project_id: str) -> PersistenceResult:
    """
    Delete project state (for 'Start New' action).

    Args:
        base_dir: Base storage directory
        project_id: Project to delete

    Returns:
        PersistenceResult
    """
    storage_dir = base_dir / "projects" / project_id

    if not storage_dir.exists():
        return PersistenceResult(success=False, error=f"Project not found: {project_id}")

    try:
        shutil.rmtree(storage_dir)
    except OSError as e:
        return PersistenceResult(success=False, error=f"Failed to delete project: {e}")

    return PersistenceResult(success=True)


def list_projects(base_dir: Path) -> list[dict]:
    """
    List all saved projects with basic metadata.

    Returns list of dicts with: project_id, topic, topic_label, profile_id,
    last_saved_at, schema_version
    """
    projects_dir = base_dir / "projects"
    if not projects_dir.exists():
        return []

    projects = []
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        state_path = project_dir / PROJECT_STATE_FILE
        if not state_path.exists():
            continue

        try:
            with open(state_path, encoding="utf-8") as f:
                data = json.load(f)

            projects.append(
                {
                    "project_id": project_dir.name,
                    "topic": data.get("topic", ""),
                    "topic_label": data.get("topic_label", ""),
                    "profile_id": data.get("profile_id", ""),
                    "duration_seconds": data.get("duration_seconds", 0),
                    "last_saved_at": data.get("last_saved_at", ""),
                    "schema_version": data.get("schema_version", "unknown"),
                }
            )
        except Exception:
            continue

    # Sort by last_saved_at descending (most recent first)
    projects.sort(key=lambda p: p.get("last_saved_at", ""), reverse=True)
    return projects


def get_active_scene_index(project: Project) -> int:
    """
    Determine the active scene index from relay state.

    Returns 0-based index of the scene that needs user action next.
    Actionable states: AWAITING_MASTER_IMAGE, AWAITING_PREVIOUS_FRAME, VIDEO_READY
    Returns 0 if no relay state or all complete.
    """
    if not project.relay_branch:
        return 0

    # Scene is "active" (needs action) if it's not CONFIRMED or COMPLETE
    # CONFIRMED = video accepted but not auto-completed yet
    # COMPLETE = fully done
    actionable_states = {
        "AWAITING_MASTER_IMAGE",
        "AWAITING_PREVIOUS_FRAME",
        "VIDEO_READY",
    }

    for i, scene in enumerate(project.scenes):
        status = project.relay_branch.scene_statuses.get(str(scene.id))
        # Handle both SceneStatus enum and string values
        status_str = status.value if hasattr(status, "value") else str(status)
        if status_str in actionable_states:
            return i

    # All scenes are CONFIRMED or COMPLETE - return last scene index
    return len(project.scenes) - 1 if project.scenes else 0


def is_project_resumable(project: Project) -> bool:
    """
    Check if a project has a valid canonical plan that can be resumed.

    Returns True if:
    - Project has scenes
    - Project has source_revision
    - Project has valid relay_branch (or can create one)
    """
    if not project.scenes:
        return False
    if not project.source_revision:
        return False
    return bool(project.profile_id)


def get_supported_schema_versions() -> list[str]:
    """Return list of supported schema versions."""
    return [CURRENT_SCHEMA_VERSION]


def migrate_project_state_if_needed(data: dict) -> dict:
    """
    Migrate project state from older schema version to current.

    Currently only supports 2.0 -> 2.0 (no migration needed).
    Future versions should implement migration logic here.
    """
    schema_version = data.get("schema_version", "1.0")

    if schema_version == CURRENT_SCHEMA_VERSION:
        return data

    # Migration logic would go here for older versions
    # For now, just return as-is and let validation handle incompatibility
    return data
