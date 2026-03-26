import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from fbuild_backend.config import settings

DB_FILENAME = "fbuild.db"


def get_database_path() -> Path:
    return settings.data_dir / DB_FILENAME


def ensure_runtime_dirs() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    settings.workspaces_dir.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    ensure_runtime_dirs()
    with sqlite3.connect(get_database_path()) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                repo_url TEXT NOT NULL UNIQUE,
                slug TEXT NOT NULL UNIQUE,
                workspace_path TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                default_branch TEXT,
                last_sync_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        _ensure_column(connection, "projects", "default_branch", "TEXT")
        _ensure_column(connection, "projects", "last_sync_at", "TEXT")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS build_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                branch TEXT NOT NULL,
                platform TEXT NOT NULL,
                status TEXT NOT NULL,
                requested_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                commit_sha TEXT,
                artifact_path TEXT,
                pgyer_url TEXT,
                error_message TEXT,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_build_jobs_status_requested_at
            ON build_jobs(status, requested_at, id)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS build_job_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                seq INTEGER NOT NULL,
                stream TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(job_id) REFERENCES build_jobs(id)
            )
            """
        )
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_build_job_logs_job_seq
            ON build_job_logs(job_id, seq)
            """
        )
        connection.commit()


def _ensure_column(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    columns = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    column_names = {column[1] for column in columns}
    if column_name in column_names:
        return

    connection.execute(
        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
    )


@contextmanager
def db_connection() -> Iterator[sqlite3.Connection]:
    ensure_runtime_dirs()
    connection = sqlite3.connect(get_database_path())
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()
