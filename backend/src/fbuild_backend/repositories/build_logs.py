from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from fbuild_backend.db import db_connection

LogStream = Literal["stdout", "stderr", "system"]


@dataclass
class BuildLogRecord:
    id: int
    job_id: int
    seq: int
    stream: LogStream
    message: str
    created_at: str


def append_build_log(job_id: int, stream: LogStream, message: str) -> BuildLogRecord:
    now = datetime.now(timezone.utc).isoformat()

    with db_connection() as connection:
        next_seq = connection.execute(
            """
            SELECT COALESCE(MAX(seq), 0) + 1
            FROM build_job_logs
            WHERE job_id = ?
            """,
            (job_id,),
        ).fetchone()[0]
        cursor = connection.execute(
            """
            INSERT INTO build_job_logs (job_id, seq, stream, message, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (job_id, next_seq, stream, message, now),
        )
        row = connection.execute(
            """
            SELECT id, job_id, seq, stream, message, created_at
            FROM build_job_logs
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    if row is None:
        raise RuntimeError("Failed to load the created build log record.")

    return BuildLogRecord(
        id=row["id"],
        job_id=row["job_id"],
        seq=row["seq"],
        stream=row["stream"],
        message=row["message"],
        created_at=row["created_at"],
    )


def list_build_logs(job_id: int, after_seq: int = 0, limit: int = 500) -> list[BuildLogRecord]:
    with db_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, job_id, seq, stream, message, created_at
            FROM build_job_logs
            WHERE job_id = ? AND seq > ?
            ORDER BY seq ASC
            LIMIT ?
            """,
            (job_id, after_seq, limit),
        ).fetchall()

    return [
        BuildLogRecord(
            id=row["id"],
            job_id=row["job_id"],
            seq=row["seq"],
            stream=row["stream"],
            message=row["message"],
            created_at=row["created_at"],
        )
        for row in rows
    ]
