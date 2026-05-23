"""IdempotencyKey — middleware-cached response for replay. Spec §4."""

from __future__ import annotations

from typing import Any

from sqlalchemy import (
    LargeBinary,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.base import BaseEntityMixin


class IdempotencyKey(BaseEntityMixin, Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("user_id", "client_idempotency_key", name="uq_idempotency_user_key"),
    )

    client_idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    response_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status_code: Mapped[int] = mapped_column(SmallInteger, nullable=False)
