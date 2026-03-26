from fastapi import APIRouter, HTTPException, status

from fbuild_backend.repositories.projects import (
    DuplicateProjectError,
    create_project,
    list_projects,
)
from fbuild_backend.schemas.projects import CreateProjectRequest, ProjectResponse

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
def get_projects() -> list[ProjectResponse]:
    return [ProjectResponse.model_validate(project) for project in list_projects()]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def post_project(payload: CreateProjectRequest) -> ProjectResponse:
    try:
        project = create_project(str(payload.repo_url))
    except DuplicateProjectError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project already exists for {exc.args[0]}",
        ) from exc

    return ProjectResponse.model_validate(project)

