from pathlib import Path
import shutil

from fbuild_backend.config import settings
from fbuild_backend.repositories.build_jobs import BuildJobRecord
from fbuild_backend.repositories.projects import ProjectRecord


class ArtifactStore:
    def archive(
        self,
        *,
        job: BuildJobRecord,
        project: ProjectRecord,
        artifact_path: str | None,
    ) -> str | None:
        if artifact_path is None:
            return None

        source = Path(artifact_path)
        if not source.exists():
            return artifact_path

        target_dir = settings.artifacts_dir / project.slug / f"job-{job.id}"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        shutil.copy2(source, target)
        return str(target)
