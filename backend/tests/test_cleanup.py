from datetime import datetime, timedelta, timezone
import os
import tempfile
import unittest
from pathlib import Path

from fbuild_backend.config import settings
from fbuild_backend.services.artifact_store import ArtifactStore
from fbuild_backend.services.cleanup import cleanup_runtime_files


class CleanupTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)

        self.original_artifacts_dir = settings.artifacts_dir
        self.original_workspaces_dir = settings.workspaces_dir

        settings.artifacts_dir = root / "artifacts"
        settings.workspaces_dir = root / "workspaces"
        settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
        settings.workspaces_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        settings.artifacts_dir = self.original_artifacts_dir
        settings.workspaces_dir = self.original_workspaces_dir
        self.temp_dir.cleanup()

    def test_cleanup_removes_old_artifacts_and_workspace_build_dirs(self) -> None:
        artifact_file = settings.artifacts_dir / "old" / "app.apk"
        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text("apk", encoding="utf-8")

        workspace_build_dir = settings.workspaces_dir / "mobile-app" / "build"
        workspace_build_dir.mkdir(parents=True, exist_ok=True)
        (workspace_build_dir / "tmp.txt").write_text("build", encoding="utf-8")

        old_timestamp = (
            datetime.now(timezone.utc) - timedelta(days=8)
        ).timestamp()
        for path in [artifact_file, workspace_build_dir, workspace_build_dir / "tmp.txt"]:
            os.utime(path, (old_timestamp, old_timestamp))

        cleanup_runtime_files(
            now=datetime.now(timezone.utc),
            artifact_retention_hours=24,
            workspace_build_retention_hours=24,
        )

        self.assertFalse(artifact_file.exists())
        self.assertFalse(workspace_build_dir.exists())

    def test_artifact_store_copies_into_managed_artifact_dir(self) -> None:
        source_dir = settings.workspaces_dir / "mobile-app"
        source_dir.mkdir(parents=True, exist_ok=True)
        source_file = source_dir / "app-release.apk"
        source_file.write_text("apk", encoding="utf-8")

        archived = ArtifactStore().archive(
            job=type("Job", (), {"id": 5})(),
            project=type("Project", (), {"slug": "mobile-app"})(),
            artifact_path=str(source_file),
        )

        self.assertIsNotNone(archived)
        self.assertTrue(Path(archived).exists())
        self.assertIn("artifacts/mobile-app/job-5", archived)


if __name__ == "__main__":
    unittest.main()
