"""BehaviorEvent — TimescaleDB hypertable for behavioral events. Spec §2 migration 0013.

Hot table — primary key is the composite ``(id, occurred_at)``. TimescaleDB
requires the partition column (``occurred_at``) in any unique constraint, so
the PK has to include it. ``id`` is uuid7 (time-ordered, probabilistically
unique); the composite gives Postgres the enforcement guarantee SQLAlchemy
expects. This matches the precedent set by migration 0001.

Notes:
- APPEND-ONLY. No ``updated_at``, no ``version``. Inherits only UUIDv7Mixin
  (for the ``id`` default) — NOT BaseEntityMixin (which assumes mutable rows).
- Coexists with the legacy ``events`` hypertable from migration 0001. Eventual
  cleanup will drop ``events``; this slice does not.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.base import UUIDv7Mixin


class BehaviorEvent(UUIDv7Mixin, Base):
    __tablename__ = "behavior_events"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True, nullable=False
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
