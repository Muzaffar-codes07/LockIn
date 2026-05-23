"""Event spine tests (spec §3)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.events.dlq import DLQRouter
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
