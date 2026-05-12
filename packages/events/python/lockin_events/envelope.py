"""Event envelope shared by every LockIn event type.

Source of truth: packages/events/src/envelope.ts. Regenerate generated.py
via `pnpm -F @lockin/events gen` after any schema change.
"""

from __future__ import annotations

from typing import Literal

EVENT_VERSION: Literal[1] = 1
EventSource = Literal["web", "mcp", "api", "agent"]
