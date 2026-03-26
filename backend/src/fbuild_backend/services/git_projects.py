from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import subprocess

from fbuild_backend.repositories.projects import ProjectRecord, update_project_sync

FIELD_SEPARATOR = "\x1f"


class GitProjectError(Exception):
    """Raised when a git command for a managed project fails."""


@dataclass
class ProjectBranchRecord:
    name: str
    commit_sha: str
    commit_date: str
    commit_subject: str


def sync_project_workspace(project: ProjectRecord) -> ProjectRecord:
    workspace_path = Path(project.workspace_path)
    workspace_path.parent.mkdir(parents=True, exist_ok=True)

    if not (workspace_path / ".git").exists():
        _run_command(
            ["git", "clone", project.repo_url, str(workspace_path)],
            cwd=workspace_path.parent,
        )
    else:
        _run_command(
            ["git", "remote", "set-url", "origin", project.repo_url],
            cwd=workspace_path,
        )

    _run_command(["git", "fetch", "--all", "--prune"], cwd=workspace_path)
    _run_command(["git", "remote", "set-head", "origin", "--auto"], cwd=workspace_path)

    default_branch = _read_default_branch(workspace_path)
    synced_at = datetime.now(timezone.utc).isoformat()
    return update_project_sync(project.id, default_branch, synced_at)


def list_project_branches(project: ProjectRecord) -> list[ProjectBranchRecord]:
    workspace_path = Path(project.workspace_path)
    if not (workspace_path / ".git").exists():
        raise GitProjectError(
            f"Workspace for project {project.id} is not ready. Sync the project first."
        )

    output = _run_command(
        [
            "git",
            "for-each-ref",
            "refs/remotes/origin",
            f"--format=%(refname:strip=3){FIELD_SEPARATOR}%(objectname:short)"
            f"{FIELD_SEPARATOR}%(committerdate:iso-strict){FIELD_SEPARATOR}%(subject)",
            "--sort=-committerdate",
        ],
        cwd=workspace_path,
    )

    branches: list[ProjectBranchRecord] = []
    for raw_line in output.splitlines():
        if not raw_line:
            continue

        name, commit_sha, commit_date, commit_subject = raw_line.split(FIELD_SEPARATOR, maxsplit=3)
        if name == "HEAD":
            continue
        branches.append(
            ProjectBranchRecord(
                name=name,
                commit_sha=commit_sha,
                commit_date=commit_date,
                commit_subject=commit_subject,
            )
        )

    return branches


def _read_default_branch(workspace_path: Path) -> str | None:
    output = _run_command(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        cwd=workspace_path,
    )
    if not output:
        return None

    prefix = "refs/remotes/origin/"
    if output.startswith(prefix):
        return output[len(prefix):]
    return output


def _run_command(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise GitProjectError(
            f"Command failed ({completed.returncode}): {' '.join(command)}\n{completed.stderr.strip()}"
        )
    return completed.stdout.strip()
