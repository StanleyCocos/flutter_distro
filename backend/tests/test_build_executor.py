import tempfile
import unittest
from pathlib import Path

from fbuild_backend.repositories.build_jobs import BuildJobRecord
from fbuild_backend.repositories.projects import ProjectRecord
from fbuild_backend.services.build_executor import BuildExecutor


class FakeCommandRunner:
    def __init__(self, workspace_path: Path) -> None:
        self.workspace_path = workspace_path
        self.commands: list[tuple[int, list[str], Path]] = []

    def run(self, job_id: int, command: list[str], cwd: Path) -> str:
        self.commands.append((job_id, command, cwd))

        if command[:3] == ["git", "rev-parse", "HEAD"]:
            return "abc123def456"

        if command[-2:] == ["build", "apk"]:
            artifact_path = (
                self.workspace_path
                / "build"
                / "app"
                / "outputs"
                / "flutter-apk"
                / "app-release.apk"
            )
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text("apk", encoding="utf-8")

        if command[-2:] == ["build", "ipa"]:
            artifact_path = self.workspace_path / "build" / "ios" / "ipa" / "app.ipa"
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text("ipa", encoding="utf-8")

        return ""


class BuildExecutorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_path = Path(self.temp_dir.name) / "workspace"
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        (self.workspace_path / "ios").mkdir(parents=True, exist_ok=True)

        self.project = ProjectRecord(
            id=1,
            name="mobile-app",
            repo_url="https://github.com/acme/mobile-app.git",
            slug="mobile-app",
            workspace_path=str(self.workspace_path),
            is_active=True,
            default_branch="main",
            last_sync_at=None,
            created_at="2026-03-26T00:00:00Z",
            updated_at="2026-03-26T00:00:00Z",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_android_execution_runs_expected_commands_and_finds_apk(self) -> None:
        job = BuildJobRecord(
            id=7,
            project_id=1,
            branch="main",
            platform="android",
            status="running",
            requested_at="2026-03-26T00:00:00Z",
            started_at="2026-03-26T00:00:01Z",
            finished_at=None,
            commit_sha=None,
            artifact_path=None,
            pgyer_url=None,
            error_message=None,
        )
        runner = FakeCommandRunner(self.workspace_path)

        result = BuildExecutor(command_runner=runner).execute(job, self.project)

        self.assertEqual(result.commit_sha, "abc123def456")
        self.assertTrue(result.artifact_path.endswith("app-release.apk"))
        self.assertEqual(
            [command for _, command, _ in runner.commands],
            [
                ["git", "fetch", "--all", "--prune"],
                ["git", "checkout", "main"],
                ["git", "reset", "--hard", "origin/main"],
                ["git", "rev-parse", "HEAD"],
                ["caffeinate", "-dimsu", "fvm", "flutter", "pub", "get"],
                ["caffeinate", "-dimsu", "fvm", "flutter", "build", "apk"],
            ],
        )

    def test_ios_execution_runs_pod_install_and_finds_ipa(self) -> None:
        job = BuildJobRecord(
            id=8,
            project_id=1,
            branch="release",
            platform="ios",
            status="running",
            requested_at="2026-03-26T00:00:00Z",
            started_at="2026-03-26T00:00:01Z",
            finished_at=None,
            commit_sha=None,
            artifact_path=None,
            pgyer_url=None,
            error_message=None,
        )
        runner = FakeCommandRunner(self.workspace_path)

        result = BuildExecutor(command_runner=runner).execute(job, self.project)

        self.assertEqual(result.commit_sha, "abc123def456")
        self.assertTrue(result.artifact_path.endswith("app.ipa"))
        self.assertIn(
            (8, ["caffeinate", "-dimsu", "pod", "install"], self.workspace_path / "ios"),
            runner.commands,
        )


if __name__ == "__main__":
    unittest.main()
