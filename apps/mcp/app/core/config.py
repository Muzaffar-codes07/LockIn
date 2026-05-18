"""MCP settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_NAME: str = "lockin-mcp"
    MCP_TRANSPORT: Literal["stdio", "sse"] = "stdio"

    API_BASE_URL: str = "http://localhost:8000"

    SSE_HOST: str = "0.0.0.0"  # noqa: S104
    SSE_PORT: int = 8081

    # Observability — same env vars as apps/api so a single secret-pull works.
    ENV: str = "local"
    APP_VERSION: str = "0.0.1"
    GIT_SHA: str = "dev"
    GRAFANA_CLOUD_OTLP_ENDPOINT: str = ""
    GRAFANA_CLOUD_OTLP_AUTH: str = ""
    SENTRY_DSN_MCP: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
