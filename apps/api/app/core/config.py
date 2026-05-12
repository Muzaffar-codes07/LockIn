"""Application settings loaded from environment.

Single global `settings` instance; import as `from app.core.config import settings`.
"""

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    APP_NAME: str = "lockin-api"
    DEBUG: bool = False

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://lockin:lockin_dev@localhost:5432/lockin"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Shared with NextAuth v5 on the web side (env var: AUTH_SECRET). The
    # legacy JWT_SECRET name is accepted for back-compat with anything that
    # already set it locally.
    JWT_SECRET: str = Field(
        default="change-me-in-production",
        validation_alias=AliasChoices("AUTH_SECRET", "JWT_SECRET"),
    )
    JWT_ALG: str = "HS256"
    JWT_TTL_SECONDS: int = 3600

    # WebAuthn (passkey) config. RP ID is the apex domain without scheme/port;
    # expected origin is the full URL the browser sees.
    WEBAUTHN_RP_ID: str = Field(default="localhost")
    WEBAUTHN_EXPECTED_ORIGIN: str = Field(default="http://localhost:3000")

    # Temporal Cloud config; localhost defaults are dev-only.
    # Provisioning a Temporal Cloud namespace is a Week 1 DevOps task per the spec.
    TEMPORAL_HOST: str = Field(default="localhost:7233")
    TEMPORAL_NAMESPACE: str = Field(default="default")
    TEMPORAL_TLS_CERT: str | None = None
    TEMPORAL_TLS_KEY: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
