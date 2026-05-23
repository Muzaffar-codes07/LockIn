"""0012 idempotency_keys."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("client_idempotency_key", sa.String(255), nullable=False),
        sa.Column("request_hash", sa.LargeBinary(), nullable=False),
        sa.Column("response_json", JSONB(), nullable=False),
        sa.Column("status_code", sa.SmallInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.UniqueConstraint("user_id", "client_idempotency_key", name="uq_idempotency_user_key"),
    )
    op.create_index("ix_idempotency_keys_tenant_id", "idempotency_keys", ["tenant_id"])
    op.create_index("ix_idempotency_keys_created_at", "idempotency_keys", ["created_at"])
    op.execute(
        "CREATE TRIGGER idempotency_keys_set_updated_at BEFORE UPDATE ON idempotency_keys "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS idempotency_keys_set_updated_at ON idempotency_keys;")
    op.drop_index("ix_idempotency_keys_created_at", table_name="idempotency_keys")
    op.drop_index("ix_idempotency_keys_tenant_id", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
