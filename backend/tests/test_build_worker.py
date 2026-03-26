import tempfile
import unittest
from pathlib import Path

from fbuild_backend import db
from fbuild_backend.config import settings
from fbuild_backend.repositories.build_jobs import create_build_job, get_build_job
from fbuild_backend.repositories.build_logs import list_build_logs
from fbuild_backend.repositories.projects import create_project
from fbuild_backend.services.build_worker import BuildWorker


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

        worker = BuildWorker()
        processed_job = worker.process_next_job()

        self.assertIsNotNone(processed_job)
        self.assertEqual(processed_job.id, queued_job.id)
        self.assertEqual(processed_job.status, "success")

        stored_job = get_build_job(queued_job.id)
        self.assertIsNotNone(stored_job)
        self.assertEqual(stored_job.status, "success")
        self.assertIsNotNone(stored_job.started_at)
        self.assertIsNotNone(stored_job.finished_at)

        log_messages = [log.message for log in list_build_logs(queued_job.id)]
        self.assertGreaterEqual(len(log_messages), 4)
        self.assertIn("Worker claimed queued job", log_messages[1])
        self.assertIn("Mock executor completed", log_messages[-1])

    def test_process_next_job_returns_none_when_queue_is_empty(self) -> None:
        worker = BuildWorker()
        self.assertIsNone(worker.process_next_job())


if __name__ == "__main__":
    unittest.main()
