from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from fbuild_backend.db import db_connection

BuildPlatform = Literal["android", "ios"]
BuildJobStatus = Literal["queued", "preparing", "running", "uploading", "success", "failed", "cancelled"]
ACTIVE_JOB_STATUSES: tuple[BuildJobStatus, ...] = ("preparing", "running", "uploading")


@dataclass
class BuildJobRecord:
    id: int
    project_id: int
    branch: str
    platform: BuildPlatform
    status: BuildJobStatus
    requested_at: str
    started_at: str | None
    finished_at: str | None
    commit_sha: str | None
    artifact_path: str | None
    pgyer_url: str | None
    error_message: str | None
    queue_position: int | None = None


def _to_record(row, queue_position: int | None = None) -> BuildJobRecord:
    return BuildJobRecord(
        id=row["id"],
        project_id=row["project_id"],
        branch=row["branch"],
        platform=row["platform"],
        status=row["status"],
        requested_at=row["requested_at"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        commit_sha=row["commit_sha"],
        artifact_path=row["artifact_path"],
        pgyer_url=row["pgyer_url"],
        error_message=row["error_message"],
        queue_position=queue_position,
    )


def create_build_job(project_id: int, branch: str, platform: BuildPlatform) -> BuildJobRecord:
    now = datetime.now(timezone.utc).isoformat()
    with db_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO build_jobs (project_id, branch, platform, status, requested_at)
            VALUES (?, ?, ?, 'queued', ?)
            """,
            (project_id, branch, platform, now),
        )
        row = connection.execute(
            """
            SELECT id, project_id, branch, platform, status, requested_at, started_at, finished_at,
                   commit_sha, artifact_path, pgyer_url, error_message
            FROM build_jobs
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    if row is None:
        raise RuntimeError("Failed to load the created build job record.")

    return _to_record(row)


def get_build_job(job_id: int) -> BuildJobRecord | None:
    with db_connection() as connection:
        row = connection.execute(
            """
            SELECT id, project_id, branch, platform, status, requested_at, started_at, finished_at,
                   commit_sha, artifact_path, pgyer_url, error_message
            FROM build_jobs
            WHERE id = ?
            """,
            (job_id,),
        ).fetchone()

    if row is None:
        return None
    return _to_record(row)


def get_current_build_job() -> BuildJobRecord | None:
    placeholders = ", ".join("?" for _ in ACTIVE_JOB_STATUSES)
    with db_connection() as connection:
        row = connection.execute(
            f"""
            SELECT id, project_id, branch, platform, status, requested_at, started_at, finished_at,
                   commit_sha, artifact_path, pgyer_url, error_message
            FROM build_jobs
            WHERE status IN ({placeholders})
            ORDER BY started_at DESC, id DESC
            LIMIT 1
            """,
            ACTIVE_JOB_STATUSES,
        ).fetchone()

    if row is None:
        return None
    return _to_record(row)


def list_queued_build_jobs() -> list[BuildJobRecord]:
    with db_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, project_id, branch, platform, status, requested_at, started_at, finished_at,
                   commit_sha, artifact_path, pgyer_url, error_message
            FROM build_jobs
            WHERE status = 'queued'
            ORDER BY requested_at ASC, id ASC
            """
        ).fetchall()

    return [_to_record(row, queue_position=index) for index, row in enumerate(rows, start=1)]

