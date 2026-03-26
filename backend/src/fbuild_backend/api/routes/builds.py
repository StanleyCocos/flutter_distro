from fastapi import APIRouter, HTTPException, status

from fbuild_backend.repositories.build_jobs import (
    create_build_job,
    get_build_job,
    get_current_build_job,
    list_queued_build_jobs,
)
from fbuild_backend.repositories.projects import get_project
from fbuild_backend.schemas.build_jobs import BuildJobResponse, CreateBuildJobRequest

router = APIRouter(prefix="/builds", tags=["builds"])


@router.post("", response_model=BuildJobResponse, status_code=status.HTTP_201_CREATED)
def post_build(payload: CreateBuildJobRequest) -> BuildJobResponse:
    project = get_project(payload.project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {payload.project_id} does not exist",
        )

    job = create_build_job(
        project_id=payload.project_id,
        branch=payload.branch,
        platform=payload.platform,
    )
    return BuildJobResponse.model_validate(job)


@router.get("/current", response_model=BuildJobResponse | None)
def get_current_build() -> BuildJobResponse | None:
    job = get_current_build_job()
    if job is None:
        return None
    return BuildJobResponse.model_validate(job)


@router.get("/queue", response_model=list[BuildJobResponse])
def get_build_queue() -> list[BuildJobResponse]:
    return [BuildJobResponse.model_validate(job) for job in list_queued_build_jobs()]


@router.get("/{job_id}", response_model=BuildJobResponse)
def get_build(job_id: int) -> BuildJobResponse:
    job = get_build_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Build job {job_id} does not exist",
        )
    return BuildJobResponse.model_validate(job)

