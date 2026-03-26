import tempfile
import unittest
from pathlib import Path

from fbuild_backend import db
from fbuild_backend.config import settings
from fbuild_backend.repositories.build_jobs import create_build_job, list_queued_build_jobs
from fbuild_backend.repositories.projects import create_project


class BuildQueueRepositoryTest(unittest.TestCase):
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

    def test_queued_jobs_are_returned_in_submission_order_with_positions(self) -> None:
        project = create_project("https://github.com/acme/mobile-app.git")
        first = create_build_job(project.id, "main", "android")
        second = create_build_job(project.id, "develop", "ios")

        queued = list_queued_build_jobs()

        self.assertEqual([job.id for job in queued], [first.id, second.id])
        self.assertEqual([job.queue_position for job in queued], [1, 2])


if __name__ == "__main__":
    unittest.main()
