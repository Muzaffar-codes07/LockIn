"""DLQ routing: when a consumer hits >3 retries, push to per-(stream, group) DLQ.

DLQ entry shape (spec §3 bend #2):
  original_id, consumer_group, error_class, failure_reason,
  first_failure_at, last_failure_at, failure_count

Streams: events:<source>:dlq:<group>. Eight DLQ streams total
(4 main x 2 groups each).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from redis.asyncio import Redis

from app.events.streams import dlq_stream

MAX_DELIVERIES = 3


class DLQRouter:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def should_route(self, delivery_count: int) -> bool:
        return delivery_count > MAX_DELIVERIES

    async def route(
        self,
        *,
        source_stream: str,
        consumer_group: str,
        original_id: str,
        original_payload: dict[str, str],
        exc: BaseException,
        first_failure_at: datetime,
        failure_count: int,
    ) -> str:
        now = datetime.now(UTC)
        entry = {
            "original_id": original_id,
            "consumer_group": consumer_group,
            "error_class": type(exc).__name__,
            "failure_reason": str(exc)[:1024],
            "first_failure_at": first_failure_at.isoformat(),
            "last_failure_at": now.isoformat(),
            "failure_count": str(failure_count),
            "original_payload": json.dumps(original_payload),
        }
        return str(await self._redis.xadd(dlq_stream(source_stream, consumer_group), entry))
