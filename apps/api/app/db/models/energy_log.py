"""EnergyLog — a user-reported energy score. Task 12 / migration 0008. Hot table (v7 ORM)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, SmallInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.base import BaseEntityMixin, UUIDv7Mixin


class EnergyLog(UUIDv7Mixin, BaseEntityMixin, Base):
    __tablename__ = "energy_logs"
    __table_args__ = (CheckConstraint("score BETWEEN 1 AND 5", name="ck_energy_logs_score"),)

    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
