from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "F-Build Backend"
    app_env: str = Field(default="development", alias="APP_ENV")
    data_dir: Path = Field(default=REPO_ROOT / "data", alias="DATA_DIR")
    logs_dir: Path = Field(default=REPO_ROOT / "logs", alias="LOGS_DIR")
    artifacts_dir: Path = Field(default=REPO_ROOT / "artifacts", alias="ARTIFACTS_DIR")
    workspaces_dir: Path = Field(default=REPO_ROOT / "workspaces", alias="WORKSPACES_DIR")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
