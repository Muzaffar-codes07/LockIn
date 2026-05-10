# TODO(mcp-slice): promote shared event schemas to packages/events/python/lockin_events/
# before the MCP slice ships (Weeks 9-10). apps/mcp will need the same types,
# so dual-maintenance ends with that promotion.

"""Python mirror of packages/events/schema.ts. Hand-maintained for now."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class EventBase(BaseModel):
    """All events versioned from day one (event_version: 1) per CLAUDE.md doctrine."""

    model_config = ConfigDict(frozen=True)

    event_version: int = 1
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
