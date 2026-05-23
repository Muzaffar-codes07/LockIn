"""0011 oauth_tokens."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "oauth_tokens",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("refresh_token_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("access_token_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("key_version", sa.SmallInteger(), nullable=False, server_default=sa.text("1")),
        sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "granted_scopes",
            sa.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "refresh_failure_count", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("sync_token", sa.String(1024), nullable=True),
        sa.Column("calendar_initial_sync_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.UniqueConstraint("user_id", "provider", name="uq_oauth_tokens_user_provider"),
    )
    op.create_index("ix_oauth_tokens_tenant_id", "oauth_tokens", ["tenant_id"])
    op.create_index("ix_oauth_tokens_key_version", "oauth_tokens", ["key_version"])
    op.execute(
        "CREATE TRIGGER oauth_tokens_set_updated_at BEFORE UPDATE ON oauth_tokens "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS oauth_tokens_set_updated_at ON oauth_tokens;")
    op.drop_index("ix_oauth_tokens_key_version", table_name="oauth_tokens")
    op.drop_index("ix_oauth_tokens_tenant_id", table_name="oauth_tokens")
    op.drop_table("oauth_tokens")
