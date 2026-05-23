"""Reaper: marks stuck stream entries eligible for retry.

NOT an owner — does not claim entries into its own consumer name.
Uses XCLAIM ... JUSTID IDLE 0 to reset the idle clock so the original
consumer picks them up on its next read.

DLQ routing is owned by the consumer (DLQRouter), not the reaper.

Spec §3 bend #1.
"""

from __future__ import annotations

from redis.asyncio import Redis

from app.core.logging import get_logger
from app.events.streams import STREAMS

logger = get_logger(__name__)

IDLE_THRESHOLD_MS = 5 * 60 * 1000


class Reaper:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def sweep_once(self) -> int:
        """Sweep every (stream, group). Returns total entries unstuck."""
        total = 0
        for spec in STREAMS:
            for group in spec.groups:
                total += await self._sweep_one(spec.name, group)
        return total

    async def _sweep_one(self, stream: str, group: str) -> int:
        pending = await self._redis.xpending_range(
            stream, group, min="-", max="+", count=100, idle=IDLE_THRESHOLD_MS
        )
        if not pending:
            return 0
        # Group entries by original consumer so we can reset their idle without
        # transferring ownership.
        by_consumer: dict[str, list[str]] = {}
        for entry in pending:
            by_consumer.setdefault(entry["consumer"], []).append(entry["message_id"])
        for consumer, ids in by_consumer.items():
            await self._redis.xclaim(
                stream,
                group,
                consumer,
                min_idle_time=0,
                message_ids=ids,
                idle=0,
                justid=True,
            )
        logger.info("reaper unstuck", stream=stream, group=group, count=len(pending))
        return len(pending)
