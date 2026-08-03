from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
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
    narrative_provider: Literal["mock", "openai"] = "mock"
    openai_api_key: SecretStr | None = None
    openai_model: str = ""
    openai_timeout_seconds: float = Field(default=30, gt=0, le=120)
    openai_max_retries: int = Field(default=2, ge=0, le=5)
    openai_fallback_to_mock: bool = True
    openai_reasoning_effort: Literal["none", "low", "medium", "high", "xhigh", "max"] | None = None
    openai_verbosity: Literal["low", "medium", "high"] | None = None

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Return normalized local origins configured for browser access."""

        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def has_openai_api_key(self) -> bool:
        """Report credential presence without exposing its value."""

        return bool(self.openai_api_key and self.openai_api_key.get_secret_value().strip())

    @property
    def has_openai_model(self) -> bool:
        return bool(self.openai_model.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
