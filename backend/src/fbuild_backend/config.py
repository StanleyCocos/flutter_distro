from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "F-Build Backend"
    app_env: str = Field(default="development", alias="APP_ENV")
    data_dir: Path = Field(default=Path("../data"), alias="DATA_DIR")
    logs_dir: Path = Field(default=Path("../logs"), alias="LOGS_DIR")
    artifacts_dir: Path = Field(default=Path("../artifacts"), alias="ARTIFACTS_DIR")
    workspaces_dir: Path = Field(default=Path("../workspaces"), alias="WORKSPACES_DIR")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
    )


settings = Settings()

