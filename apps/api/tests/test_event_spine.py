"""Event spine tests (spec §3)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

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
