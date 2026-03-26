from dataclasses import dataclass
from datetime import datetime, timezone
import sqlite3

from fbuild_backend.config import settings
from fbuild_backend.db import db_connection
from fbuild_backend.utils.projects import derive_project_name, slugify_project_name


@dataclass
class ProjectRecord:
    id: int
    name: str
    repo_url: str
    slug: str
    workspace_path: str
    is_active: bool
    last_sync_at: str | None
    created_at: str
    updated_at: str


class DuplicateProjectError(Exception):
    """Raised when a project already exists."""


def _to_record(row: sqlite3.Row) -> ProjectRecord:
    return ProjectRecord(
        id=row["id"],
        name=row["name"],
        repo_url=row["repo_url"],
        slug=row["slug"],
        workspace_path=row["workspace_path"],
        is_active=bool(row["is_active"]),
        last_sync_at=row["last_sync_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def list_projects() -> list[ProjectRecord]:
    with db_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, repo_url, slug, workspace_path, is_active, last_sync_at, created_at, updated_at
            FROM projects
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()
    return [_to_record(row) for row in rows]


def _next_available_slug(base_slug: str) -> str:
    with db_connection() as connection:
        rows = connection.execute(
            """
            SELECT slug
            FROM projects
            WHERE slug = ? OR slug LIKE ?
            ORDER BY slug ASC
            """,
            (base_slug, f"{base_slug}-%"),
        ).fetchall()

    existing = {row["slug"] for row in rows}
    if base_slug not in existing:
        return base_slug

    suffix = 2
    while f"{base_slug}-{suffix}" in existing:
        suffix += 1
    return f"{base_slug}-{suffix}"


def create_project(repo_url: str) -> ProjectRecord:
    now = datetime.now(timezone.utc).isoformat()
    name = derive_project_name(repo_url)
    slug = _next_available_slug(slugify_project_name(name))
    workspace_path = str(settings.workspaces_dir / slug)

    try:
        with db_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO projects (name, repo_url, slug, workspace_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, repo_url, slug, workspace_path, now, now),
            )
            row = connection.execute(
                """
                SELECT id, name, repo_url, slug, workspace_path, is_active, last_sync_at, created_at, updated_at
                FROM projects
                WHERE id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise DuplicateProjectError(repo_url) from exc

    if row is None:
        raise RuntimeError("Failed to load the created project record.")

    return _to_record(row)
