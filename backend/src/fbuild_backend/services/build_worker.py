from fbuild_backend.repositories.build_jobs import (
    BuildJobRecord,
    claim_next_queued_build_job,
    update_build_job,
)
from fbuild_backend.repositories.build_logs import append_build_log


class BuildWorker:
    """Single-job processor used by the future background queue loop."""

    def process_next_job(self) -> BuildJobRecord | None:
        job = claim_next_queued_build_job()
        if job is None:
            return None

        append_build_log(job.id, "system", "Worker claimed queued job and started preparation.")
        job = update_build_job(job.id, status="running")
        append_build_log(job.id, "system", "Mock executor entered running state.")

        # This foundation keeps the execution mock-only for now.
        job = update_build_job(job.id, status="uploading")
        append_build_log(job.id, "system", "Mock executor entered uploading state.")

        job = update_build_job(job.id, status="success")
        append_build_log(job.id, "system", "Mock executor completed the build successfully.")
        return job
