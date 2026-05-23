"""Validates TimescaleDB aggregate query latency and compression engagement.

Requires the seed script to have been run; if rows < 100k the tests xfail.
"""

from __future__ import annotations

import time

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


@pytest.mark.integration
@pytest.mark.asyncio
async def test_aggregate_query_under_100ms() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        count_row = await conn.execute(text("SELECT count(*) FROM behavior_events"))
        if count_row.scalar_one() < 100_000:
            pytest.xfail("Seed script not run; <100k rows in behavior_events")

        # Warm OS page cache + plan cache.
        await conn.execute(
            text(
                "SELECT user_id, sum(completions) "
                "FROM daily_task_completions "
                "WHERE day > now() - interval '30 days' "
                "GROUP BY user_id"
            )
        )

        start = time.perf_counter()
        await conn.execute(
            text(
                "SELECT user_id, sum(completions) "
                "FROM daily_task_completions "
                "WHERE day > now() - interval '30 days' "
                "GROUP BY user_id"
            )
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 100, f"aggregate query took {elapsed_ms:.1f}ms"
    await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_compression_engages_on_backdated_chunk() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        chunks = await conn.execute(
            text(
                "SELECT chunk_schema || '.' || chunk_name AS chunk "
                "FROM timescaledb_information.chunks "
                "WHERE hypertable_name = 'behavior_events' "
                "AND range_end < now() - interval '7 days' "
                "ORDER BY range_end LIMIT 1"
            )
        )
        row = chunks.fetchone()
        if row is None:
            pytest.xfail("No backdated chunks; seed older data or extend script window")
        # Force compression (the policy is async; we want a synchronous check).
        await conn.execute(text(f"SELECT compress_chunk('{row.chunk}')"))
        check = await conn.execute(
            text(
                "SELECT is_compressed FROM timescaledb_information.chunks " "WHERE chunk_name = :n"
            ),
            {"n": row.chunk.split(".")[-1]},
        )
        assert check.scalar_one() is True
    await engine.dispose()
