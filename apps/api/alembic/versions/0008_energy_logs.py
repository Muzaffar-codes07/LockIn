"""0008 energy_logs."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "energy_logs",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("logged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.SmallInteger(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("score BETWEEN 1 AND 5", name="ck_energy_logs_score"),
    )
    op.create_index("ix_energy_logs_tenant_id", "energy_logs", ["tenant_id"])
    op.create_index(
        "ix_energy_logs_user_id_logged_at",
        "energy_logs",
        ["user_id", sa.text("logged_at DESC"), sa.text("id DESC")],
    )
    op.execute(
        "CREATE TRIGGER energy_logs_set_updated_at BEFORE UPDATE ON energy_logs "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS energy_logs_set_updated_at ON energy_logs;")
    op.drop_index("ix_energy_logs_user_id_logged_at", table_name="energy_logs")
    op.drop_index("ix_energy_logs_tenant_id", table_name="energy_logs")
    op.drop_table("energy_logs")
