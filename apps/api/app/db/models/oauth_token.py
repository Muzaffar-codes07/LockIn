"""OAuthToken — per-(user, provider) refresh/access tokens, AES-GCM encrypted. Spec §5."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID  # noqa: F401  (used implicitly by BaseEntityMixin)

from sqlalchemy import (
    ARRAY,
    DateTime,
    Integer,
    LargeBinary,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.base import BaseEntityMixin


class OAuthToken(BaseEntityMixin, Base):
    __tablename__ = "oauth_tokens"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_oauth_tokens_user_provider"),
    )

    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    refresh_token_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    access_token_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    key_version: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="1", index=False
    )
    access_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    granted_scopes: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}"
    )
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refresh_failure_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    sync_token: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    calendar_initial_sync_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
