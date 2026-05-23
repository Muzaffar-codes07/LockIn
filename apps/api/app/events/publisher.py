"""Backwards-compat re-export. Prefer importing from app.events.streams."""

from redis.asyncio import Redis

from app.core.config import settings
from app.events.streams import EventPublisher, StreamRegistry

__all__ = ["EventPublisher", "StreamRegistry", "get_redis"]


def get_redis() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)
