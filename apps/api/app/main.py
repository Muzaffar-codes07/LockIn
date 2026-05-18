"""FastAPI application factory + lifespan.

`app` at module scope is what uvicorn imports (`uvicorn app.main:app`).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.observability import configure_observability


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging("DEBUG" if settings.DEBUG else "INFO")
    logger = get_logger("app.startup")
    logger.info("startup", app=settings.APP_NAME)
    try:
        yield
    finally:
        logger.info("shutdown", app=settings.APP_NAME)


def create_app() -> FastAPI:
    fast_app = FastAPI(title="LockIn API", version=settings.APP_VERSION, lifespan=lifespan)
    register_exception_handlers(fast_app)
    configure_observability(fast_app)
    fast_app.include_router(api_router)

    # Liveness route at root, matching the Dockerfile HEALTHCHECK probe path.
    # /v1/health remains the canonical versioned endpoint for clients.
    @fast_app.get("/health", include_in_schema=False)
    async def _root_health() -> dict[str, str]:
        return {"status": "ok"}

    return fast_app


app = create_app()
