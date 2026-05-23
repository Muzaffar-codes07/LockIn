"""Shared SQLAlchemy mixins for the standard row shape (Week 3-4 §2)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import uuid_utils
from sqlalchemy import DateTime, Integer, func, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


def _uuid7() -> UUID:
    """UUID v7 generator — time-ordered, used as ORM default on hot tables.

    Hot path: this fires on every ORM INSERT for behavior_events / tasks /
    mood_logs / energy_logs, so we go through .bytes (one alloc) rather than
    the str roundtrip (two allocs).
    """
    return UUID(bytes=uuid_utils.uuid7().bytes)


class BaseEntityMixin:
    """Standard row shape from spec §2.

    Every domain table in Week 3-4 inherits this. `id` defaults to v4 at the
    server (raw-SQL fallback); hot-table subclasses override the ORM default
    to uuid7 via UUIDv7Mixin so writes from Python are time-ordered.
    """

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    tenant_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"), nullable=False)


class UUIDv7Mixin:
    """Hot-table override: ORM-side uuid7 default. Server still has v4 fallback."""

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=_uuid7,
        server_default=text("gen_random_uuid()"),
    )
