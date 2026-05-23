"""CalendarEvent — Google Calendar event ingested via read-only sync. Spec §2 migration 0010."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.base import BaseEntityMixin


class CalendarEvent(BaseEntityMixin, Base):
    __tablename__ = "calendar_events"
    __table_args__ = (
        UniqueConstraint("user_id", "google_event_id", name="uq_calendar_events_user_google_id"),
    )

    google_event_id: Mapped[str] = mapped_column(String(1024), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    etag: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_calendar_id: Mapped[str] = mapped_column(
        String(256), nullable=False, server_default="primary"
    )
