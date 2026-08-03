from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent
DEFAULT_DATABASE_URL = f"sqlite:///{BACKEND_ROOT / 'data' / 'multiverse.db'}"


class Settings(BaseSettings):
    """Backend configuration loaded from environment variables."""

    app_name: str = "Multiverse API"
    app_version: str = "0.1.0"
    app_env: str = "development"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    backend_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_url: str = DEFAULT_DATABASE_URL
    narrative_provider: Literal["mock"] = "mock"

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Return normalized local origins configured for browser access."""

        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
