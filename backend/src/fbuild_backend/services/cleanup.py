from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil

from fbuild_backend.config import settings


def cleanup_runtime_files(
    *,
    now: datetime | None = None,
    artifact_retention_hours: int | None = None,
    workspace_build_retention_hours: int | None = None,
) -> None:
    now = now or datetime.now(timezone.utc)
    artifact_retention = timedelta(
        hours=artifact_retention_hours
        if artifact_retention_hours is not None
        else settings.artifact_retention_hours
    )
    workspace_retention = timedelta(
        hours=workspace_build_retention_hours
        if workspace_build_retention_hours is not None
        else settings.workspace_build_retention_hours
    )

    _cleanup_tree(settings.artifacts_dir, now - artifact_retention)

    for workspace in settings.workspaces_dir.iterdir():
        if not workspace.is_dir():
            continue
        build_dir = workspace / "build"
        if build_dir.exists() and _is_older_than(build_dir, now - workspace_retention):
            shutil.rmtree(build_dir, ignore_errors=True)


def _cleanup_tree(root: Path, threshold: datetime) -> None:
    if not root.exists():
        return

    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file() and _is_older_than(path, threshold):
            path.unlink(missing_ok=True)
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def _is_older_than(path: Path, threshold: datetime) -> bool:
    modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return modified_at < threshold
