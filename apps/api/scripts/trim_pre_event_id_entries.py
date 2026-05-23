"""One-shot: trim pre-event_id entries from events:tasks.

Defensible because Slice 0 was local-dev-only with no consumers running yet.
Executed as part of §3 deploy. Spec §3 bend #4.

Usage: cd apps/api && uv run python scripts/trim_pre_event_id_entries.py
"""

from __future__ import annotations

import asyncio
import time

from app.events.publisher import get_redis


async def main() -> None:
    cutoff_ms = int(time.time() * 1000)
    redis = get_redis()
    try:
        # MINID drops entries with stream IDs older than the given timestamp.
        # We use cutoff - 60s as a safety margin so we don't accidentally trim
        # entries that arrived during this script's execution.
        trimmed = await redis.xtrim("events:tasks", minid=cutoff_ms - 60_000)
        print(f"Trimmed {trimmed} entries from events:tasks (cutoff {cutoff_ms - 60_000})")
    finally:
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
