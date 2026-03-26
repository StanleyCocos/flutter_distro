from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "F-Build Backend"
    app_env: str = Field(default="development", alias="APP_ENV")
    pgyer_api_key: str = Field(default="", alias="PGYER_API_KEY")
    pgyer_install_type: str = Field(default="1", alias="PGYER_INSTALL_TYPE")
    pgyer_poll_attempts: int = Field(default=60, alias="PGYER_POLL_ATTEMPTS")
    pgyer_poll_seconds: float = Field(default=1.0, alias="PGYER_POLL_SECONDS")
    worker_poll_seconds: float = Field(default=2.0, alias="WORKER_POLL_SECONDS")
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
