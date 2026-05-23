"""0004 migration hygiene baseline.

Pairs with the same-commit edit to ``apps/api/app/db/models/task.py`` that
flips the ORM default from ``uuid4`` to ``uuid_utils.uuid7``. The server
default below (``gen_random_uuid()`` = v4) is a fallback for raw SQL
inserts. App-side writes are v7. Existing rows are NOT rewritten.

Also extends ``ix_tasks_user_id`` to the standard
``(user_id, created_at DESC, id DESC)`` shape from spec §2.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Server-side UUID defaults (v4 fallback for raw SQL).
    op.execute("ALTER TABLE tasks ALTER COLUMN id SET DEFAULT gen_random_uuid()")
    op.execute("ALTER TABLE webauthn_credentials " "ALTER COLUMN id SET DEFAULT gen_random_uuid()")

    # Replace the single-column index with the standard composite.
    op.drop_index("ix_tasks_user_id", table_name="tasks")
    op.create_index(
        "ix_tasks_user_id_created_at",
        "tasks",
        ["user_id", sa.text("created_at DESC"), sa.text("id DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_tasks_user_id_created_at", table_name="tasks")
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"])
    op.execute("ALTER TABLE webauthn_credentials ALTER COLUMN id DROP DEFAULT")
    op.execute("ALTER TABLE tasks ALTER COLUMN id DROP DEFAULT")
