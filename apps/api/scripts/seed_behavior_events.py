"""Generate 1M synthetic behavior_events across 10 users x 90 days.

Used to validate that the continuous aggregate query stays <100ms after refresh
and that compression engages on backdated chunks. Spec §2 acceptance criteria.

Usage: cd apps/api && uv run python scripts/seed_behavior_events.py
"""

from __future__ import annotations

import asyncio
import json
import random
from datetime import UTC, datetime, timedelta
from uuid import UUID

import uuid_utils
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

USERS = [UUID(str(uuid_utils.uuid7())) for _ in range(10)]
EVENT_TYPES = ["task.created", "task.completed", "mood.logged", "energy.logged"]
BATCH_SIZE = 5000
TOTAL_EVENTS = 1_000_000


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    start = datetime.now(UTC) - timedelta(days=90)
    rows_remaining = TOTAL_EVENTS

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE behavior_events"))

    inserted = 0
    while rows_remaining > 0:
        n = min(BATCH_SIZE, rows_remaining)
        # Build parameter rows
        rows = []
        for _ in range(n):
            user = random.choice(USERS)  # noqa: S311
            event_type = random.choice(EVENT_TYPES)  # noqa: S311
            offset_seconds = random.randint(0, 90 * 86400)  # noqa: S311
            occurred_at = start + timedelta(seconds=offset_seconds)
            payload = (
                {"score": random.randint(1, 5)} if event_type == "mood.logged" else {}  # noqa: S311
            )
            rows.append(
                {
                    "id": str(uuid_utils.uuid7()),
                    "user_id": str(user),
                    "event_type": event_type,
                    "occurred_at": occurred_at,
                    "payload": json.dumps(payload),
                }
            )
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO behavior_events "
                    "(id, user_id, event_type, occurred_at, payload) "
                    "VALUES (:id, :user_id, :event_type, :occurred_at, CAST(:payload AS jsonb))"
                ),
                rows,
            )
        inserted += n
        rows_remaining -= n
        print(f"  inserted {inserted:>9,}/{TOTAL_EVENTS:,}")

    # refresh_continuous_aggregate must run outside a transaction block.
    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(
            text("CALL refresh_continuous_aggregate('daily_task_completions', NULL, NULL)")
        )
        await conn.execute(text("CALL refresh_continuous_aggregate('daily_mood_avg', NULL, NULL)"))
    print("Aggregates refreshed.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
