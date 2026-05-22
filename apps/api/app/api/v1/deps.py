"""FastAPI dependency providers: DB sessions, Redis, event publisher."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.events.publisher import EventPublisher, get_redis


async def _db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(_db_session)]


async def _redis() -> AsyncIterator[Redis]:
    redis = get_redis()
    try:
        yield redis
    finally:
        await redis.aclose()


RedisDep = Annotated[Redis, Depends(_redis)]


async def _event_publisher(redis: RedisDep) -> EventPublisher:
    return EventPublisher(redis)


EventPublisherDep = Annotated[EventPublisher, Depends(_event_publisher)]
