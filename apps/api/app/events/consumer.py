"""Redis Streams consumer scaffold. Workers/projections wire onto this per slice."""
from collections.abc import AsyncIterator
from typing import Any

from redis.asyncio import Redis


class EventConsumer:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def read(
        self,
        stream: str,
        *,
        last_id: str = "$",
        block_ms: int = 5000,
        count: int = 10,
    ) -> AsyncIterator[tuple[str, dict[str, Any]]]:
        while True:
            messages = await self._redis.xread({stream: last_id}, block=block_ms, count=count)
            if not messages:
                continue
            for _stream_name, entries in messages:
                for message_id, fields in entries:
                    yield message_id, fields
                    last_id = message_id
