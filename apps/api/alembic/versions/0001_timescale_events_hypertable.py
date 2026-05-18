"""timescale events hypertable

Revision ID: 0001
Revises:
Create Date: 2026-05-12

Defines the canonical event-sourced ``events`` table as a TimescaleDB
hypertable. Behavior-graph writes from every slice land here. This migration
is committed but **must be applied manually** the first time Week 3 hits the
write path, after the CREATE EXTENSION step described in
``infra/terraform/README.md``.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    op.create_table(
        "events",
        sa.Column("event_id", UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("event_version", sa.Integer, nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("client_idempotency_key", sa.String(128), nullable=True),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.PrimaryKeyConstraint("event_id", "occurred_at"),
    )

    op.execute(
        "SELECT create_hypertable("
        "'events', 'occurred_at', chunk_time_interval => INTERVAL '7 days'"
        ")"
    )

    op.create_index("ix_events_user_occurred", "events", ["user_id", "occurred_at"])
    op.create_index("ix_events_type_occurred", "events", ["event_type", "occurred_at"])
    op.create_unique_constraint(
        "uq_events_user_idem",
        "events",
        ["user_id", "client_idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_events_user_idem", "events", type_="unique")
    op.drop_index("ix_events_type_occurred", table_name="events")
    op.drop_index("ix_events_user_occurred", table_name="events")
    op.drop_table("events")
