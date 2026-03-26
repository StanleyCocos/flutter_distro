import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from fbuild_backend.config import settings
from fbuild_backend.main import app


class BuildApiTest(unittest.TestCase):
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

    def tearDown(self) -> None:
        settings.data_dir = self.original_data_dir
        settings.logs_dir = self.original_logs_dir
        settings.artifacts_dir = self.original_artifacts_dir
        settings.workspaces_dir = self.original_workspaces_dir
        self.temp_dir.cleanup()

    def test_create_build_job_and_read_queue(self) -> None:
        with TestClient(app) as client:
            project_response = client.post(
                "/api/projects",
                json={"repo_url": "https://github.com/acme/mobile-app.git"},
            )
            self.assertEqual(project_response.status_code, 201)

            build_response = client.post(
                "/api/builds",
                json={
                    "project_id": project_response.json()["id"],
                    "branch": "main",
                    "platform": "android",
                },
            )
            self.assertEqual(build_response.status_code, 201)
            self.assertEqual(build_response.json()["status"], "queued")

            queue_response = client.get("/api/builds/queue")
            self.assertEqual(queue_response.status_code, 200)
            self.assertEqual(len(queue_response.json()), 1)
            self.assertEqual(queue_response.json()[0]["queue_position"], 1)


if __name__ == "__main__":
    unittest.main()
