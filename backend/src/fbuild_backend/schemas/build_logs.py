from typing import Literal

from pydantic import BaseModel, ConfigDict

LogStream = Literal["stdout", "stderr", "system"]


class BuildLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    seq: int
    stream: LogStream
    message: str
    created_at: str
