"""Shared pytest fixtures."""

from collections.abc import AsyncIterator

import fakeredis.aioredis
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.db.models  # noqa: F401 -- registers all models on Base.metadata
from app.api.v1.deps import _db_session, _redis
from app.core.config import settings
from app.db.base import Base
from app.main import app


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    # raise_app_exceptions=False makes uncaught exceptions surface as 500
    # responses, matching production ASGI servers.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _test_db_url() -> str:
    """Derive the test DB URL from DATABASE_URL by swapping the database name."""
    base, _, _name = settings.DATABASE_URL.rpartition("/")
    if not base:
        raise ValueError(f"Cannot derive test DB URL from DATABASE_URL={settings.DATABASE_URL!r}")
    return f"{base}/lockin_test"


@pytest_asyncio.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(_test_db_url(), future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def fake_redis() -> AsyncIterator[fakeredis.aioredis.FakeRedis]:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield redis
    await redis.aclose()


@pytest_asyncio.fixture
async def db_client(
    db_engine: AsyncEngine,
    fake_redis: fakeredis.aioredis.FakeRedis,
) -> AsyncIterator[AsyncClient]:
    """An HTTP client whose API uses the test DB and an in-memory Redis."""
    maker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_db() -> AsyncIterator[AsyncSession]:
        async with maker() as session:
            yield session

    async def _override_redis() -> AsyncIterator[Redis]:
        yield fake_redis

    app.dependency_overrides[_db_session] = _override_db
    app.dependency_overrides[_redis] = _override_redis

    try:
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()
