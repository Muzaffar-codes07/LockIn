"""Redis Streams: publisher + stream/group registry + dedup pattern.

CONSUMER-SIDE DEDUP PATTERN (frozen here so Week 5+ consumers inherit one shape):
  SADD consumer:<group>:seen <event_id> EX 86400 NX
  If 0 → already seen, ack and skip.
  If 1 → process, then XACK.

Streams + groups are created idempotently at app startup via StreamRegistry.bootstrap().
Spec §3.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel
from redis.asyncio import Redis
from redis.exceptions import ResponseError

logger = logging.getLogger(__name__)

DEFAULT_MAXLEN = 100_000  # spec §5 bend #6


@dataclass(frozen=True)
class StreamSpec:
    name: str
    groups: tuple[str, ...]


STREAMS: tuple[StreamSpec, ...] = (
    StreamSpec("events:tasks", ("capture-svc", "analytics-svc")),
    StreamSpec("events:mood_energy", ("capture-svc", "analytics-svc")),
    StreamSpec("events:calendar", ("scheduler-svc", "analytics-svc")),
    StreamSpec("events:agent", ("agent-svc", "analytics-svc")),
)


def dlq_stream(source: str, group: str) -> str:
    return f"{source}:dlq:{group}"


EventClass = Literal["behavioral", "operational"]


class EventPublisher:
    """Typed publisher. Callers pick behavioral vs operational at the call site."""

    def __init__(self, redis: Redis, *, maxlen: int = DEFAULT_MAXLEN) -> None:
        self._redis = redis
        self._maxlen = maxlen

    async def publish_behavioral(self, stream: str, event: BaseModel) -> str:
        """Publish a behavioral event. Week 5+ consumers also insert into behavior_events."""
        return await self._xadd(stream, event, kind="behavioral")

    async def publish_operational(self, stream: str, event: BaseModel) -> str:
        """Publish an operational event. Stream-only; never enters behavior_events."""
        return await self._xadd(stream, event, kind="operational")

    async def _xadd(self, stream: str, event: BaseModel, *, kind: EventClass) -> str:
        # event_id must be on the event envelope (lockin_events base contract).
        event_id = getattr(event, "event_id", None)
        if event_id is None:
            raise ValueError(f"{type(event).__name__} missing event_id; cannot publish")
        msg_id = await self._redis.xadd(
            stream,
            {
                "event_id": str(event_id),
                "kind": kind,
                "data": event.model_dump_json(),
            },
            maxlen=self._maxlen,
            approximate=True,
        )
        return str(msg_id)


class StreamRegistry:
    """Idempotent bootstrap of streams + consumer groups (spec §3)."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def bootstrap(self) -> None:
        for spec in STREAMS:
            for group in spec.groups:
                try:
                    await self._redis.xgroup_create(spec.name, group, id="$", mkstream=True)
                    logger.info(
                        "created consumer group", extra={"stream": spec.name, "group": group}
                    )
                except ResponseError as e:
                    if "BUSYGROUP" not in str(e):
                        raise
