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
    fast_app = FastAPI(title="LockIn API", version="0.0.1", lifespan=lifespan)
    register_exception_handlers(fast_app)
    fast_app.include_router(api_router)
    return fast_app


app = create_app()
