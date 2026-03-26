from collections.abc import Callable

from fbuild_backend.repositories.projects import get_project, ProjectRecord
from fbuild_backend.services.artifact_store import ArtifactStore
from fbuild_backend.services.build_executor import BuildExecutor
from fbuild_backend.services.pgyer_uploader import (
    MockPgyerUploader,
    PgyerUploader,
    create_default_uploader,
)
from fbuild_backend.services.git_projects import sync_project_workspace
from fbuild_backend.repositories.build_jobs import (
    BuildJobRecord,
    claim_next_queued_build_job,
    update_build_job,
)
from fbuild_backend.repositories.build_logs import append_build_log


class BuildWorker:
    """Single-job processor used by the future background queue loop."""

    def __init__(
        self,
        *,
        build_executor: BuildExecutor | None = None,
        project_syncer: Callable[[ProjectRecord], ProjectRecord] | None = None,
        uploader: PgyerUploader | MockPgyerUploader | None = None,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
        self._build_executor = build_executor or BuildExecutor()
        self._project_syncer = project_syncer or sync_project_workspace
        self._uploader = uploader or create_default_uploader()
        self._artifact_store = artifact_store or ArtifactStore()

    def process_next_job(self) -> BuildJobRecord | None:
        job = claim_next_queued_build_job()
        if job is None:
            return None

        append_build_log(job.id, "system", "Worker claimed queued job and started preparation.")
        try:
            project = self._load_project(job.project_id)
            append_build_log(job.id, "system", f"Syncing workspace for project {project.slug}.")
            synced_project = self._project_syncer(project)

            job = update_build_job(job.id, status="running")
            append_build_log(job.id, "system", "Workspace synced. Starting build commands.")
            result = self._build_executor.execute(job, synced_project)
            archived_artifact_path = self._artifact_store.archive(
                job=job,
                project=synced_project,
                artifact_path=result.artifact_path,
            )

            job = update_build_job(
                job.id,
                status="uploading",
                commit_sha=result.commit_sha,
                artifact_path=archived_artifact_path,
            )
            append_build_log(job.id, "system", "Build finished. Starting Pgyer upload.")
            upload_result = self._uploader.upload(
                job=job,
                project=synced_project,
                artifact_path=archived_artifact_path,
            )

            job = update_build_job(job.id, status="success", pgyer_url=upload_result.download_url)
            append_build_log(job.id, "system", "Build worker completed the job successfully.")
            return job
        except Exception as exc:
            append_build_log(job.id, "stderr", str(exc))
            failed_job = update_build_job(job.id, status="failed", error_message=str(exc))
            append_build_log(job.id, "system", "Build worker marked the job as failed.")
            return failed_job

    def _load_project(self, project_id: int) -> ProjectRecord:
        project = get_project(project_id)
        if project is None:
            raise RuntimeError(f"Project {project_id} does not exist for this build job.")
        return project
