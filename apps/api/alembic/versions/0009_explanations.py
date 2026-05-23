"""0009 explanations."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "explanations",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("subject_type", sa.String(32), nullable=False),
        sa.Column("subject_id", UUID(as_uuid=True), nullable=False),
        sa.Column("reasoning", JSONB, nullable=False),
        sa.Column("model_id", sa.String(64), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
    )
    op.create_index("ix_explanations_tenant_id", "explanations", ["tenant_id"])
    op.create_index(
        "ix_explanations_user_id_created_at",
        "explanations",
        ["user_id", sa.text("created_at DESC"), sa.text("id DESC")],
    )
    op.execute(
        "CREATE TRIGGER explanations_set_updated_at BEFORE UPDATE ON explanations "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS explanations_set_updated_at ON explanations;")
    op.drop_index("ix_explanations_user_id_created_at", table_name="explanations")
    op.drop_index("ix_explanations_tenant_id", table_name="explanations")
    op.drop_table("explanations")
