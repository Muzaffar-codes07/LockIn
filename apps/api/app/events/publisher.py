"""Redis Streams publisher. Always called by services after a successful DB commit."""

from pydantic import BaseModel
from redis.asyncio import Redis

from app.core.config import settings


class EventPublisher:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def publish(self, stream: str, event: BaseModel) -> str:
        """Publish any pydantic event model to a Redis Stream.

        Accepts BaseModel rather than a LockIn-specific base so this publisher
        is decoupled from the event-package class hierarchy. The canonical
        event types live in ``lockin_events`` and all inherit from BaseModel.
        """
        message_id = await self._redis.xadd(stream, {"data": event.model_dump_json()})
        return str(message_id)


def get_redis() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)
