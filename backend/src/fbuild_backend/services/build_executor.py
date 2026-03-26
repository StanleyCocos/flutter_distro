from dataclasses import dataclass
from pathlib import Path
import subprocess

from fbuild_backend.repositories.build_jobs import BuildJobRecord
from fbuild_backend.repositories.build_logs import append_build_log
from fbuild_backend.repositories.projects import ProjectRecord


class BuildExecutionError(Exception):
    """Raised when one of the build commands fails."""


@dataclass
class BuildExecutionResult:
    commit_sha: str
    artifact_path: str | None


class CommandRunner:
    """Runs shell commands for a build job."""

    def run(self, job_id: int, command: list[str], cwd: Path) -> str:
        append_build_log(job_id, "system", f"$ {' '.join(command)}")
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        for line in completed.stdout.splitlines():
            append_build_log(job_id, "stdout", line)
        for line in completed.stderr.splitlines():
            append_build_log(job_id, "stderr", line)
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            raise BuildExecutionError(
                f"Command failed ({completed.returncode}): {' '.join(command)}\n{stderr}"
            )
        return completed.stdout.strip()


class BuildExecutor:
    def __init__(self, command_runner: CommandRunner | None = None) -> None:
        self._command_runner = command_runner or CommandRunner()

    def execute(self, job: BuildJobRecord, project: ProjectRecord) -> BuildExecutionResult:
        workspace_path = Path(project.workspace_path)
        commit_sha = self._prepare_branch(workspace_path, job.branch, job.id)
        self._run_flutter_prep(workspace_path, job.id)

        if job.platform == "ios":
            self._run_ios_build(workspace_path, job.id)
        else:
            self._run_android_build(workspace_path, job.id)

        artifact_path = self._detect_artifact_path(workspace_path, job.platform)
        return BuildExecutionResult(commit_sha=commit_sha, artifact_path=artifact_path)

    def _prepare_branch(self, workspace_path: Path, branch: str, job_id: int) -> str:
        self._command_runner.run(job_id, ["git", "fetch", "--all", "--prune"], workspace_path)
        self._command_runner.run(job_id, ["git", "checkout", branch], workspace_path)
        self._command_runner.run(
            job_id,
            ["git", "reset", "--hard", f"origin/{branch}"],
            workspace_path,
        )
        return self._command_runner.run(job_id, ["git", "rev-parse", "HEAD"], workspace_path)

    def _run_flutter_prep(self, workspace_path: Path, job_id: int) -> None:
        self._command_runner.run(job_id, ["caffeinate", "-dimsu", "fvm", "flutter", "pub", "get"], workspace_path)

    def _run_android_build(self, workspace_path: Path, job_id: int) -> None:
        self._command_runner.run(
            job_id,
            ["caffeinate", "-dimsu", "fvm", "flutter", "build", "apk"],
            workspace_path,
        )

    def _run_ios_build(self, workspace_path: Path, job_id: int) -> None:
        ios_path = workspace_path / "ios"
        self._command_runner.run(
            job_id,
            ["caffeinate", "-dimsu", "pod", "install"],
            ios_path,
        )
        self._command_runner.run(
            job_id,
            ["caffeinate", "-dimsu", "fvm", "flutter", "build", "ipa"],
            workspace_path,
        )

    def _detect_artifact_path(self, workspace_path: Path, platform: str) -> str | None:
        if platform == "android":
            artifact_path = workspace_path / "build" / "app" / "outputs" / "flutter-apk" / "app-release.apk"
            return str(artifact_path) if artifact_path.exists() else None

        ipa_dir = workspace_path / "build" / "ios" / "ipa"
        ipa_files = sorted(ipa_dir.glob("*.ipa"))
        if ipa_files:
            return str(ipa_files[0])
        return None
