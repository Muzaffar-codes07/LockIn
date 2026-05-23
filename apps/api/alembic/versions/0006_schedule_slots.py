"""0006 schedule_slots."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "schedule_slots",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "task_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.SmallInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
    )
    op.create_index("ix_schedule_slots_tenant_id", "schedule_slots", ["tenant_id"])
    op.create_index(
        "ix_schedule_slots_user_id_scheduled_for",
        "schedule_slots",
        ["user_id", "scheduled_for"],
    )
    op.execute(
        "CREATE TRIGGER schedule_slots_set_updated_at BEFORE UPDATE ON schedule_slots "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS schedule_slots_set_updated_at ON schedule_slots;")
    op.drop_index("ix_schedule_slots_user_id_scheduled_for", table_name="schedule_slots")
    op.drop_index("ix_schedule_slots_tenant_id", table_name="schedule_slots")
    op.drop_table("schedule_slots")
