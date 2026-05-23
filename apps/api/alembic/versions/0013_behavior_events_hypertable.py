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
    # Composite PRIMARY KEY (id, occurred_at) — matches the migration 0001
    # precedent and the only PK shape TimescaleDB accepts for hypertables.
    # The partition column (occurred_at) must be part of any unique constraint,
    # so we make it part of the PK. id alone has no DB-level uniqueness but
    # is uuid7 (probabilistically unique); the composite PK gives Postgres
    # the enforcement guarantee the ORM expects.
    op.execute(
        """
        CREATE TABLE behavior_events (
            id          UUID        NOT NULL DEFAULT gen_random_uuid(),
            user_id     UUID        NOT NULL,
            event_type  VARCHAR(64) NOT NULL,
            occurred_at TIMESTAMPTZ NOT NULL,
            payload     JSONB       NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id, occurred_at)
        );
        """
    )
    op.execute(
        "SELECT create_hypertable('behavior_events', 'occurred_at', "
        "chunk_time_interval => INTERVAL '1 month');"
    )
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
    op.drop_table("behavior_events")
