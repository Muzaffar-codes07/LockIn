"""MCP settings."""
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


settings = Settings()
