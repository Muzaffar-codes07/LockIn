"""0005 tasks expansion: tenant_id, updated_at, version, status."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("tenant_id", UUID(as_uuid=True), nullable=True))
    op.create_index("ix_tasks_tenant_id", "tasks", ["tenant_id"])
    op.add_column(
        "tasks",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column(
        "tasks", sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False)
    )
    op.add_column(
        "tasks",
        sa.Column("status", sa.String(16), server_default=sa.text("'captured'"), nullable=False),
    )
    op.create_check_constraint(
        "ck_tasks_status",
        "tasks",
        "status IN ('captured', 'scheduled', 'in_progress', 'completed', 'cancelled')",
    )
    # Trigger so updated_at advances on every UPDATE without ORM cooperation.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
        BEGIN
          NEW.updated_at = now();
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        "CREATE TRIGGER tasks_set_updated_at BEFORE UPDATE ON tasks "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS tasks_set_updated_at ON tasks;")
    # Intentionally do NOT drop set_updated_at(): subsequent tables
    # (mood_logs, energy_logs, schedule_slots, etc.) reuse it via their own
    # BEFORE UPDATE triggers. Dropping it here would cascade-break those
    # triggers on any partial downgrade. The function is effectively a
    # shared utility owned by the schema, not by this migration.
    op.drop_constraint("ck_tasks_status", "tasks", type_="check")
    op.drop_column("tasks", "status")
    op.drop_column("tasks", "version")
    op.drop_column("tasks", "updated_at")
    op.drop_index("ix_tasks_tenant_id", table_name="tasks")
    op.drop_column("tasks", "tenant_id")
