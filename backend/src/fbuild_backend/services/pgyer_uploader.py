from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any, Callable, Protocol

import httpx

from fbuild_backend.config import settings
from fbuild_backend.repositories.build_jobs import BuildJobRecord
from fbuild_backend.repositories.projects import ProjectRecord

TOKEN_URL = "https://www.pgyer.com/apiv2/app/getCOSToken"
BUILD_INFO_URL = "https://www.pgyer.com/apiv2/app/buildInfo"
DEFAULT_BASE_URL = "https://www.pgyer.com"


class HttpClient(Protocol):
    def post(self, url: str, **kwargs: Any) -> httpx.Response: ...

    def get(self, url: str, **kwargs: Any) -> httpx.Response: ...


@dataclass
class UploadResult:
    download_url: str
    build_key: str


class PgyerUploadError(Exception):
    """Raised when the Pgyer upload flow fails."""


class PgyerUploader:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        install_type: str | None = None,
        poll_attempts: int | None = None,
        poll_seconds: float | None = None,
        http_client: HttpClient | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else settings.pgyer_api_key
        self._install_type = install_type if install_type is not None else settings.pgyer_install_type
        self._poll_attempts = poll_attempts if poll_attempts is not None else settings.pgyer_poll_attempts
        self._poll_seconds = poll_seconds if poll_seconds is not None else settings.pgyer_poll_seconds
        self._http_client = http_client or httpx.Client(timeout=60.0)
        self._sleep = sleep or time.sleep

    def upload(
        self,
        *,
        job: BuildJobRecord,
        project: ProjectRecord,
        artifact_path: str | None,
    ) -> UploadResult:
        if not self._api_key:
            raise PgyerUploadError("PGYER_API_KEY is not configured.")
        if not artifact_path:
            raise PgyerUploadError("No build artifact was produced for upload.")

        artifact_file = Path(artifact_path)
        if not artifact_file.exists():
            raise PgyerUploadError(f"Build artifact does not exist: {artifact_path}")

        build_type = artifact_file.suffix.lstrip(".").lower()
        if build_type not in {"apk", "ipa"}:
            raise PgyerUploadError(f"Unsupported artifact type for Pgyer upload: {build_type}")

        token_data = self._get_upload_token(build_type, job, project)
        build_key = token_data["key"]
        endpoint = token_data["endpoint"]
        self._upload_file(endpoint, token_data, artifact_file)
        build_info = self._poll_build_info(build_key)
        shortcut = build_info.get("buildShortcutUrl") or build_key
        download_url = shortcut if shortcut.startswith("http") else f"{DEFAULT_BASE_URL}/{shortcut}"
        return UploadResult(download_url=download_url, build_key=build_key)

    def _get_upload_token(
        self,
        build_type: str,
        job: BuildJobRecord,
        project: ProjectRecord,
    ) -> dict[str, str]:
        response = self._http_client.post(
            TOKEN_URL,
            data={
                "_api_key": self._api_key,
                "buildType": build_type,
                "buildInstallType": self._install_type,
                "buildUpdateDescription": f"{project.name} {job.branch} #{job.id}",
            },
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") or {}
        required_fields = ("endpoint", "key", "signature", "x-cos-security-token")
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            raise PgyerUploadError(f"Pgyer token response is missing fields: {', '.join(missing)}")
        return data

    def _upload_file(self, endpoint: str, token_data: dict[str, str], artifact_file: Path) -> None:
        with artifact_file.open("rb") as file_handle:
            response = self._http_client.post(
                endpoint,
                data={
                    "key": token_data["key"],
                    "signature": token_data["signature"],
                    "x-cos-security-token": token_data["x-cos-security-token"],
                    "x-cos-meta-file-name": artifact_file.name,
                },
                files={"file": (artifact_file.name, file_handle, _guess_content_type(artifact_file))},
            )

        if response.status_code != 204:
            raise PgyerUploadError(
                f"Pgyer object storage upload failed with HTTP {response.status_code}: {response.text}"
            )

    def _poll_build_info(self, build_key: str) -> dict[str, Any]:
        for _ in range(self._poll_attempts):
            response = self._http_client.get(
                BUILD_INFO_URL,
                params={"_api_key": self._api_key, "buildKey": build_key},
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("code") == 0:
                data = payload.get("data") or {}
                if not isinstance(data, dict):
                    raise PgyerUploadError("Unexpected Pgyer buildInfo response format.")
                return data
            self._sleep(self._poll_seconds)

        raise PgyerUploadError("Timed out while waiting for Pgyer to process the uploaded build.")


class MockPgyerUploader:
    def upload(
        self,
        *,
        job: BuildJobRecord,
        project: ProjectRecord,
        artifact_path: str | None,
    ) -> UploadResult:
        artifact_name = Path(artifact_path).name if artifact_path else "no-artifact"
        return UploadResult(
            download_url=(
                f"https://mock.pgyer.local/apps/{project.slug}/"
                f"{job.platform}/{job.id}?artifact={artifact_name}"
            ),
            build_key=f"mock-{job.id}",
        )


def create_default_uploader() -> PgyerUploader | MockPgyerUploader:
    return PgyerUploader() if settings.pgyer_api_key else MockPgyerUploader()


def _guess_content_type(artifact_file: Path) -> str:
    suffix = artifact_file.suffix.lower()
    if suffix == ".apk":
        return "application/vnd.android.package-archive"
    if suffix == ".ipa":
        return "application/octet-stream"
    return "application/octet-stream"
