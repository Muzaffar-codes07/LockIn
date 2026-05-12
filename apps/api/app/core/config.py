"""Application settings loaded from environment.

Single global `settings` instance; import as `from app.core.config import settings`.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_NAME: str = "lockin-api"
    DEBUG: bool = False

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://lockin:lockin_dev@localhost:5432/lockin"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    JWT_SECRET: str = Field(default="change-me-in-production")
    JWT_ALG: str = "HS256"
    JWT_TTL_SECONDS: int = 3600

    # Temporal Cloud config; localhost defaults are dev-only.
    # Provisioning a Temporal Cloud namespace is a Week 1 DevOps task per the spec.
    TEMPORAL_HOST: str = Field(default="localhost:7233")
    TEMPORAL_NAMESPACE: str = Field(default="default")
    TEMPORAL_TLS_CERT: str | None = None
    TEMPORAL_TLS_KEY: str | None = None

    # Observability. Leaving the OTLP endpoint / Sentry DSN empty disables
    # those exporters — handy in tests and local dev where there's no
    # collector running.
    ENV: str = Field(default="local")
    APP_VERSION: str = Field(default="0.0.1")
    GIT_SHA: str = Field(default="dev")
    GRAFANA_CLOUD_OTLP_ENDPOINT: str = Field(default="")
    GRAFANA_CLOUD_OTLP_AUTH: str = Field(default="")
    SENTRY_DSN_API: str = Field(default="")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
