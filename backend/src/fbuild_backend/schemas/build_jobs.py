from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

BuildPlatform = Literal["android", "ios"]
BuildJobStatus = Literal["queued", "preparing", "running", "uploading", "success", "failed", "cancelled"]


class CreateBuildJobRequest(BaseModel):
    project_id: int
    branch: str
    platform: BuildPlatform

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("branch must not be empty")
        return cleaned


class BuildJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    branch: str
    platform: BuildPlatform
    status: BuildJobStatus
    requested_at: str
    started_at: str | None
    finished_at: str | None
    commit_sha: str | None
    artifact_path: str | None
    pgyer_url: str | None
    error_message: str | None
    queue_position: int | None = None

