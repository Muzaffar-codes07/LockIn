"""0013 behavior_events hypertable + continuous aggregates.

Coexists with the legacy `events` hypertable from migration 0001. The two
tables have different schemas and serve different purposes: `events` is a
generic event log (composite PK on event_id+occurred_at); `behavior_events`
is the analytical store powering daily aggregates. A future cleanup
migration will drop `events`.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Use raw SQL for table creation: Alembic's create_table emits a UNIQUE index
    # on `id` (the PK), but TimescaleDB refuses unique indexes that don't include
    # the partition column (occurred_at). We drop the PK constraint immediately
    # after hypertable creation and re-add it as a non-unique index so id remains
    # a fast lookup column without violating TimescaleDB partitioning rules.
    op.execute(
        """
        CREATE TABLE behavior_events (
            id          UUID        NOT NULL DEFAULT gen_random_uuid(),
            user_id     UUID        NOT NULL,
            event_type  VARCHAR(64) NOT NULL,
            occurred_at TIMESTAMPTZ NOT NULL,
            payload     JSONB       NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(
        "SELECT create_hypertable('behavior_events', 'occurred_at', "
        "chunk_time_interval => INTERVAL '1 month');"
    )
    # After hypertable creation, add a non-unique index on id for fast point lookups.
    op.execute("CREATE INDEX ix_behavior_events_id ON behavior_events (id);")
    op.execute(
        "CREATE INDEX ix_behavior_events_user_type_occurred "
        "ON behavior_events (user_id, event_type, occurred_at DESC);"
    )
    op.execute(
        "ALTER TABLE behavior_events SET ("
        "timescaledb.compress, "
        "timescaledb.compress_segmentby = 'user_id, event_type'"
        ");"
    )
    op.execute("SELECT add_compression_policy('behavior_events', INTERVAL '7 days');")
    # Continuous aggregate: daily task completions per user.
    op.execute(
        """
        CREATE MATERIALIZED VIEW daily_task_completions
        WITH (timescaledb.continuous) AS
        SELECT
          user_id,
          time_bucket('1 day', occurred_at) AS day,
          count(*) AS completions
        FROM behavior_events
        WHERE event_type = 'task.completed'
        GROUP BY user_id, day
        WITH NO DATA;
        """
    )
    op.execute(
        "SELECT add_continuous_aggregate_policy('daily_task_completions', "
        "start_offset => INTERVAL '7 days', "
        "end_offset => INTERVAL '1 hour', "
        "schedule_interval => INTERVAL '15 minutes');"
    )
    # Continuous aggregate: daily mood average per user.
    op.execute(
        """
        CREATE MATERIALIZED VIEW daily_mood_avg
        WITH (timescaledb.continuous) AS
        SELECT
          user_id,
          time_bucket('1 day', occurred_at) AS day,
          avg((payload->>'score')::float) AS avg_score
        FROM behavior_events
        WHERE event_type = 'mood.logged'
        GROUP BY user_id, day
        WITH NO DATA;
        """
    )
    op.execute(
        "SELECT add_continuous_aggregate_policy('daily_mood_avg', "
        "start_offset => INTERVAL '7 days', "
        "end_offset => INTERVAL '1 hour', "
        "schedule_interval => INTERVAL '15 minutes');"
    )
    # Retention policy: documented but NOT registered for P1.
    # When enforced (P2+), run:
    #   SELECT add_retention_policy('behavior_events', INTERVAL '90 days');


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS daily_mood_avg CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS daily_task_completions CASCADE;")
    op.execute("SELECT remove_compression_policy('behavior_events', if_exists => true);")
    op.execute("DROP INDEX IF EXISTS ix_behavior_events_user_type_occurred;")
    op.execute("DROP INDEX IF EXISTS ix_behavior_events_id;")
    op.drop_table("behavior_events")
