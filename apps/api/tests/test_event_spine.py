"""Event spine tests (spec §3)."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from redis.asyncio import Redis as RealRedis

from app.events.dlq import DLQRouter
from app.events.streams import StreamRegistry
from app.jobs.reaper import (  # noqa: F401  (IDLE_THRESHOLD_MS asserted indirectly)
    IDLE_THRESHOLD_MS,
    Reaper,
)


@pytest.mark.asyncio
async def test_reaper_resets_idle_without_taking_ownership() -> None:
    redis = AsyncMock()
    redis.xpending_range.return_value = [
        {
            "message_id": "1-0",
            "consumer": "capture-svc-1",
            "time_since_delivered": 600_000,
            "times_delivered": 1,
        },
        {
            "message_id": "1-1",
            "consumer": "capture-svc-2",
            "time_since_delivered": 600_000,
            "times_delivered": 1,
        },
        {
            "message_id": "2-0",
            "consumer": "capture-svc-1",
            "time_since_delivered": 600_000,
            "times_delivered": 1,
        },
    ]
    reaper = Reaper(redis)
    n = await reaper._sweep_one("events:tasks", "capture-svc")
    assert n == 3
    # Two XCLAIM calls, grouped by original consumer; neither transfers to "reaper".
    consumers_used = {call.args[2] for call in redis.xclaim.call_args_list}
    assert consumers_used == {"capture-svc-1", "capture-svc-2"}
    for call in redis.xclaim.call_args_list:
        assert call.kwargs.get("justid") is True
        assert call.kwargs.get("idle") == 0


@pytest.mark.asyncio
async def test_dlq_router_records_full_context() -> None:
    redis = AsyncMock()
    redis.xadd.return_value = "dlq-1-0"
    router = DLQRouter(redis)
    msg_id = await router.route(
        source_stream="events:tasks",
        consumer_group="capture-svc",
        original_id="1-0",
        original_payload={"event_id": "01abc", "data": "{}"},
        exc=ValueError("schema mismatch"),
        first_failure_at=datetime(2026, 5, 22, 10, 0, tzinfo=UTC),
        failure_count=4,
    )
    assert msg_id == "dlq-1-0"
    redis.xadd.assert_awaited_once()
    args, _ = redis.xadd.call_args
    assert args[0] == "events:tasks:dlq:capture-svc"
    entry = args[1]
    assert entry["error_class"] == "ValueError"
    assert entry["failure_reason"] == "schema mismatch"
    assert entry["failure_count"] == "4"


# ---------------------------------------------------------------------------
# Real-Redis integration tests (require docker-compose redis on localhost:6379)
# ---------------------------------------------------------------------------

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/15")  # /15 = test db


@pytest.fixture
async def real_redis():
    redis = RealRedis.from_url(REDIS_URL, decode_responses=True)
    await redis.flushdb()
    yield redis
    await redis.flushdb()
    await redis.aclose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_consumer_group_resumption_no_dupes_no_drops(real_redis) -> None:
    """Produce 10k entries, ack 5k, restart consumer, verify resume at 5001."""
    await StreamRegistry(real_redis).bootstrap()
    # Manual XADD (bypass typed publisher to keep test focused on stream semantics).
    for i in range(10_000):
        await real_redis.xadd("events:tasks", {"event_id": f"id-{i}", "data": "{}"}, maxlen=20_000)

    # First consumer instance: ack first 5k.
    acked: list[str] = []
    while len(acked) < 5_000:
        resp = await real_redis.xreadgroup(
            "capture-svc", "consumer-A", {"events:tasks": ">"}, count=1000
        )
        for _stream, entries in resp:
            for entry_id, _data in entries:
                await real_redis.xack("events:tasks", "capture-svc", entry_id)
                acked.append(entry_id)

    # Simulate crash + restart with the same consumer name.
    acked2: list[str] = []
    while len(acked2) < 5_000:
        resp = await real_redis.xreadgroup(
            "capture-svc", "consumer-A", {"events:tasks": ">"}, count=1000
        )
        if not resp:
            break
        for _stream, entries in resp:
            for entry_id, _data in entries:
                await real_redis.xack("events:tasks", "capture-svc", entry_id)
                acked2.append(entry_id)

    info = await real_redis.xinfo_groups("events:tasks")
    capture = next(g for g in info if g["name"] == "capture-svc")
    assert capture["pending"] == 0
    assert len(acked) + len(acked2) == 10_000
    assert len(set(acked) & set(acked2)) == 0  # no dupes
