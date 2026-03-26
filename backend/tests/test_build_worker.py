import tempfile
import unittest
from pathlib import Path

from fbuild_backend import db
from fbuild_backend.config import settings
from fbuild_backend.repositories.build_jobs import create_build_job, get_build_job
from fbuild_backend.repositories.build_logs import list_build_logs
from fbuild_backend.repositories.projects import create_project, get_project
from fbuild_backend.services.build_executor import BuildExecutionResult
from fbuild_backend.services.build_worker import BuildWorker


class FakeBuildExecutor:
    def __init__(self, *, artifact_suffix: str = "app-release.apk", fail_with: str | None = None) -> None:
        self.artifact_suffix = artifact_suffix
        self.fail_with = fail_with
        self.calls: list[tuple[int, int]] = []

    def execute(self, job, project) -> BuildExecutionResult:
        if self.fail_with is not None:
            raise RuntimeError(self.fail_with)

        self.calls.append((job.id, project.id))
        return BuildExecutionResult(
            commit_sha="abc123def456",
            artifact_path=f"{project.workspace_path}/{self.artifact_suffix}",
        )


class BuildWorkerTest(unittest.TestCase):
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

        db.init_db()

    def tearDown(self) -> None:
        settings.data_dir = self.original_data_dir
        settings.logs_dir = self.original_logs_dir
        settings.artifacts_dir = self.original_artifacts_dir
        settings.workspaces_dir = self.original_workspaces_dir
        self.temp_dir.cleanup()

    def test_process_next_job_advances_job_to_success_with_logs(self) -> None:
        project = create_project("https://github.com/acme/mobile-app.git")
        queued_job = create_build_job(project.id, "main", "android")
        stored_project = get_project(project.id)
        self.assertIsNotNone(stored_project)

        fake_executor = FakeBuildExecutor()

        worker = BuildWorker(
            build_executor=fake_executor,
            project_syncer=lambda input_project: input_project,
        )
        processed_job = worker.process_next_job()

        self.assertIsNotNone(processed_job)
        self.assertEqual(processed_job.id, queued_job.id)
        self.assertEqual(processed_job.status, "success")
        self.assertEqual(processed_job.commit_sha, "abc123def456")
        self.assertTrue(processed_job.artifact_path.endswith("app-release.apk"))
        self.assertEqual(fake_executor.calls, [(queued_job.id, project.id)])

        stored_job = get_build_job(queued_job.id)
        self.assertIsNotNone(stored_job)
        self.assertEqual(stored_job.status, "success")
        self.assertIsNotNone(stored_job.started_at)
        self.assertIsNotNone(stored_job.finished_at)
        self.assertEqual(stored_job.commit_sha, "abc123def456")

        log_messages = [log.message for log in list_build_logs(queued_job.id)]
        self.assertGreaterEqual(len(log_messages), 5)
        self.assertIn("Worker claimed queued job", log_messages[1])
        self.assertIn("Build worker completed", log_messages[-1])

    def test_process_next_job_returns_none_when_queue_is_empty(self) -> None:
        worker = BuildWorker()
        self.assertIsNone(worker.process_next_job())

    def test_process_next_job_marks_failure_when_executor_raises(self) -> None:
        project = create_project("https://github.com/acme/mobile-app.git")
        queued_job = create_build_job(project.id, "main", "android")

        worker = BuildWorker(
            build_executor=FakeBuildExecutor(fail_with="simulated build failure"),
            project_syncer=lambda input_project: input_project,
        )
        processed_job = worker.process_next_job()

        self.assertIsNotNone(processed_job)
        self.assertEqual(processed_job.status, "failed")
        self.assertEqual(processed_job.error_message, "simulated build failure")

        log_messages = [log.message for log in list_build_logs(queued_job.id)]
        self.assertIn("simulated build failure", log_messages[-2])
        self.assertIn("marked the job as failed", log_messages[-1])


if __name__ == "__main__":
    unittest.main()
