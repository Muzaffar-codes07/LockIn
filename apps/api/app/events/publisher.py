"""Redis Streams publisher. Always called by services after a successful DB commit."""

from redis.asyncio import Redis

from app.core.config import settings
from app.events.schemas import EventBase


class EventPublisher:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def publish(self, stream: str, event: EventBase) -> str:
        message_id = await self._redis.xadd(stream, {"data": event.model_dump_json()})
        return str(message_id)


def get_redis() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)
