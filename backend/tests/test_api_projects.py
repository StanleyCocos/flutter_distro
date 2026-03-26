import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from fbuild_backend import db
from fbuild_backend.config import settings
from fbuild_backend.main import app
from fbuild_backend.repositories.projects import create_project


class ProjectApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)

        self.original_data_dir = settings.data_dir
        self.original_logs_dir = settings.logs_dir
        self.original_artifacts_dir = settings.artifacts_dir
        self.original_workspaces_dir = settings.workspaces_dir

        settings.data_dir = root / "data"
        settings.logs_dir = root / "logs"
        settings.artifacts_dir = root / "artifacts"
        settings.workspaces_dir = root / "workspaces"

        self.remote_dir = root / "remote.git"
        self.seed_dir = root / "seed"

        db.init_db()
        self._create_remote_repository()

    def tearDown(self) -> None:
        settings.data_dir = self.original_data_dir
        settings.logs_dir = self.original_logs_dir
        settings.artifacts_dir = self.original_artifacts_dir
        settings.workspaces_dir = self.original_workspaces_dir
        self.temp_dir.cleanup()

    def test_sync_endpoint_updates_project_and_returns_branches(self) -> None:
        project = create_project(str(self.remote_dir))

        with TestClient(app) as client:
            sync_response = client.post(f"/api/projects/{project.id}/sync")
            self.assertEqual(sync_response.status_code, 200)
            self.assertEqual(sync_response.json()["default_branch"], "main")

            branches_response = client.get(f"/api/projects/{project.id}/branches")
            self.assertEqual(branches_response.status_code, 200)
            self.assertEqual(
                [item["name"] for item in branches_response.json()],
                ["feature/login", "main"],
            )

    def _create_remote_repository(self) -> None:
        self._run_git(["git", "init", "--bare", str(self.remote_dir)])
        self._run_git(["git", "init", str(self.seed_dir)])
        self._run_git(["git", "checkout", "-b", "main"], cwd=self.seed_dir)
        self._run_git(["git", "config", "user.name", "Codex"], cwd=self.seed_dir)
        self._run_git(["git", "config", "user.email", "codex@example.com"], cwd=self.seed_dir)

        (self.seed_dir / "README.md").write_text("main branch\n", encoding="utf-8")
        self._run_git(["git", "add", "README.md"], cwd=self.seed_dir)
        self._run_git(["git", "commit", "-m", "init main"], cwd=self.seed_dir)
        self._run_git(["git", "remote", "add", "origin", str(self.remote_dir)], cwd=self.seed_dir)
        self._run_git(["git", "push", "-u", "origin", "main"], cwd=self.seed_dir)

        self._run_git(["git", "checkout", "-b", "feature/login"], cwd=self.seed_dir)
        (self.seed_dir / "login.txt").write_text("feature branch\n", encoding="utf-8")
        self._run_git(["git", "add", "login.txt"], cwd=self.seed_dir)
        self._run_git(["git", "commit", "-m", "add login"], cwd=self.seed_dir)
        self._run_git(["git", "push", "-u", "origin", "feature/login"], cwd=self.seed_dir)
        self._run_git(["git", "checkout", "main"], cwd=self.seed_dir)
        self._run_git(["git", "remote", "set-head", "origin", "main"], cwd=self.seed_dir)

        shutil.rmtree(self.seed_dir)

    def _run_git(self, command: list[str], cwd: Path | None = None) -> None:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(
                f"Command failed ({completed.returncode}): {' '.join(command)}\n{completed.stderr}"
            )


if __name__ == "__main__":
    unittest.main()
