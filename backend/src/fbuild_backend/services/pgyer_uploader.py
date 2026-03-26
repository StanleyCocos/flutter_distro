from dataclasses import dataclass
from pathlib import Path

from fbuild_backend.repositories.build_jobs import BuildJobRecord
from fbuild_backend.repositories.projects import ProjectRecord


@dataclass
class UploadResult:
    download_url: str


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
            )
        )
