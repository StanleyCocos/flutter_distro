from fastapi import APIRouter, HTTPException, status

from fbuild_backend.repositories.projects import (
    DuplicateProjectError,
    create_project,
    get_project,
    list_projects,
)
from fbuild_backend.schemas.projects import (
    CreateProjectRequest,
    ProjectBranchResponse,
    ProjectResponse,
)
from fbuild_backend.services.git_projects import (
    GitProjectError,
    list_project_branches,
    sync_project_workspace,
)

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


@router.post("/{project_id}/sync", response_model=ProjectResponse)
def post_project_sync(project_id: int) -> ProjectResponse:
    project = get_project(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} does not exist",
        )

    try:
        synced_project = sync_project_workspace(project)
    except GitProjectError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ProjectResponse.model_validate(synced_project)


@router.get("/{project_id}/branches", response_model=list[ProjectBranchResponse])
def get_project_branches(project_id: int) -> list[ProjectBranchResponse]:
    project = get_project(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} does not exist",
        )

    try:
        branches = list_project_branches(project)
    except GitProjectError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return [ProjectBranchResponse.model_validate(branch.__dict__) for branch in branches]
