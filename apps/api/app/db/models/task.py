"""Task rows — a user-captured unit of work.

Slice 0 keeps this table intentionally minimal (YAGNI). Week 3–4 Scaffolding
owns the expansion (`tenant_id`, `version`, `status`, indexes). Do not add
those columns here.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False, server_default="keyboard")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
