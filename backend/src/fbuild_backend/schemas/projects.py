from pydantic import BaseModel, ConfigDict, field_validator


class CreateProjectRequest(BaseModel):
    repo_url: str

    @field_validator("repo_url")
    @classmethod
    def validate_repo_url(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("repo_url must not be empty")
        if not cleaned.startswith(("http://", "https://", "git@")):
            raise ValueError("repo_url must be an HTTPS/HTTP or SSH Git address")
        return cleaned


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    repo_url: str
    slug: str
    workspace_path: str
    is_active: bool
    default_branch: str | None
    last_sync_at: str | None
    created_at: str
    updated_at: str


class ProjectBranchResponse(BaseModel):
    name: str
    commit_sha: str
    commit_date: str
    commit_subject: str
