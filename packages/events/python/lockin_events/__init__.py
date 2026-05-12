"""LockIn event schema — Python types.

Canonical source lives in TypeScript at packages/events/src/schema.ts. The
``generated`` module is overwritten by ``pnpm -F @lockin/events gen``. Import
errors here mean the codegen step has not been run yet on this checkout.
"""

from lockin_events.envelope import EVENT_VERSION, EventSource
from lockin_events.streams import (
    EVENT_TYPE_TO_STREAM,
    STREAM_AGENT,
    STREAM_SCHEDULE,
    STREAM_SIGNALS,
    STREAM_TASKS,
)

try:
    from lockin_events.generated import *  # noqa: F401,F403
except ImportError as exc:  # pragma: no cover - dev-time guidance
    raise ImportError(
        "lockin_events.generated is missing. Run `pnpm -F @lockin/events gen` "
        "to produce it from packages/events/src/schema.ts."
    ) from exc

__all__ = [
    "EVENT_TYPE_TO_STREAM",
    "EVENT_VERSION",
    "EventSource",
    "STREAM_AGENT",
    "STREAM_SCHEDULE",
    "STREAM_SIGNALS",
    "STREAM_TASKS",
]
