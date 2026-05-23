"""ScheduleSlot — a time-window allocation for a Task. Spec §2 migration 0006."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.base import BaseEntityMixin


class ScheduleSlot(BaseEntityMixin, Base):
    __tablename__ = "schedule_slots"

    task_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False)
