from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "YouTube Downloader API"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    download_dir: str = str(Path.home() / "ytdownloader_tmp")
    max_file_age_seconds: int = 600
    cleanup_interval_seconds: int = 120

    cors_origins: str = "*"
    log_level: str = "INFO"

    rate_limit_rpm: int = 30

    @property
    def download_path(self) -> Path:
        path = Path(self.download_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
