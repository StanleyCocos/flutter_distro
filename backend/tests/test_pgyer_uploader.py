import tempfile
import unittest
from pathlib import Path

import httpx

from fbuild_backend.repositories.build_jobs import BuildJobRecord
from fbuild_backend.repositories.projects import ProjectRecord
from fbuild_backend.services.pgyer_uploader import PgyerUploader, PgyerUploadError


class FakeHttpClient:
    def __init__(self) -> None:
        self.posts: list[tuple[str, dict]] = []
        self.gets: list[tuple[str, dict]] = []
        self._build_info_calls = 0

    def post(self, url: str, **kwargs):
        self.posts.append((url, kwargs))
        if "getCOSToken" in url:
            return httpx.Response(
                200,
                request=httpx.Request("POST", url),
                json={
                    "code": 0,
                    "data": {
                        "endpoint": "https://cos.mock/upload",
                        "key": "build-key-123",
                        "signature": "sig",
                        "x-cos-security-token": "token",
                    },
                },
            )
        return httpx.Response(204, request=httpx.Request("POST", url), text="")

    def get(self, url: str, **kwargs):
        self.gets.append((url, kwargs))
        self._build_info_calls += 1
        if self._build_info_calls == 1:
            return httpx.Response(
                200,
                request=httpx.Request("GET", url),
                json={"code": 1247, "message": "processing"},
            )
        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            json={"code": 0, "data": {"buildShortcutUrl": "abcxyz"}},
        )


class PgyerUploaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        artifact_dir = Path(self.temp_dir.name)
        self.artifact_path = artifact_dir / "app-release.apk"
        self.artifact_path.write_text("apk", encoding="utf-8")

        self.job = BuildJobRecord(
            id=5,
            project_id=2,
            branch="main",
            platform="android",
            status="uploading",
            requested_at="2026-03-26T00:00:00Z",
            started_at="2026-03-26T00:00:01Z",
            finished_at=None,
            commit_sha="abc123",
            artifact_path=str(self.artifact_path),
            pgyer_url=None,
            error_message=None,
        )
        self.project = ProjectRecord(
            id=2,
            name="mobile-app",
            repo_url="https://github.com/acme/mobile-app.git",
            slug="mobile-app",
            workspace_path="/tmp/mobile-app",
            is_active=True,
            default_branch="main",
            last_sync_at=None,
            created_at="2026-03-26T00:00:00Z",
            updated_at="2026-03-26T00:00:00Z",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_upload_runs_token_upload_and_poll_flow(self) -> None:
        fake_http = FakeHttpClient()
        uploader = PgyerUploader(
            api_key="demo-key",
            http_client=fake_http,
            poll_attempts=3,
            poll_seconds=0,
            sleep=lambda _: None,
        )

        result = uploader.upload(
            job=self.job,
            project=self.project,
            artifact_path=str(self.artifact_path),
        )

        self.assertEqual(result.build_key, "build-key-123")
        self.assertEqual(result.download_url, "https://www.pgyer.com/abcxyz")
        self.assertEqual(len(fake_http.posts), 2)
        self.assertEqual(len(fake_http.gets), 2)

    def test_upload_requires_existing_artifact(self) -> None:
        uploader = PgyerUploader(
            api_key="demo-key",
            http_client=FakeHttpClient(),
            poll_attempts=1,
            poll_seconds=0,
            sleep=lambda _: None,
        )

        with self.assertRaises(PgyerUploadError):
            uploader.upload(
                job=self.job,
                project=self.project,
                artifact_path=str(self.artifact_path.parent / "missing.apk"),
            )


if __name__ == "__main__":
    unittest.main()
