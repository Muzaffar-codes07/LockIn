# Week 3-4 Scaffolding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the six scaffolding deliverables from the Week 3-4 handoff — Postgres tables + Alembic chain, TimescaleDB hypertable + continuous aggregates, Redis Streams event spine, API gateway middleware stack, Google Calendar read-only polling sync, and the responsive frontend shell — leaving Week 5-6 ready to wire the capture loop without re-scaffolding.

**Architecture:** Single feature branch `feat/week-3-4-scaffolding`, six logical commits matching the six deliverables, squash-merge at end-of-slice. Local-first pragmatic substrate (Docker `timescale/timescaledb:2.17.2-pg16` on `:5433`, Redis on `:6379`). All schema changes go through Alembic (including APScheduler's jobstore via migration `0014`). Event spine separates **behavioral** (feeds `behavior_events` hypertable) from **operational** (stream-only) at the `EventPublisher` API surface. Calendar sync is APScheduler-driven polling with a fenced Redis lock and `asyncio.timeout(280)` inside the lock window.

**Tech Stack:** FastAPI · SQLAlchemy 2.0 async + asyncpg · Alembic · TimescaleDB 2.17 · Redis 7.4 + Streams · APScheduler 3.x (AsyncIOScheduler + SQLAlchemyJobStore) · `uuid-utils` (Rust/PyO3) · `cryptography` (AES-GCM) · `sse-starlette` · Next.js 16 App Router · NextAuth v5 · TanStack Query v5 · Tailwind · Radix UI Dialog · `@microsoft/fetch-event-source` · `vitest-axe` · Lighthouse CI · Storybook 10.

**Driving spec:** [`docs/superpowers/specs/2026-05-22-week-3-4-scaffolding-design.md`](../specs/2026-05-22-week-3-4-scaffolding-design.md) — read it first; every task below references a spec section.

---

## Foundation gate (verify before Task 1)

Local-first pragmatic posture per spec §1. Confirm on a clean checkout:

- [ ] `pnpm install` completes; `pnpm typecheck` + `pnpm lint` clean on `main`
- [ ] `docker ps` shows no container bound to `5433` (we're about to claim it)
- [ ] Native PG18 on `:5432` left alone — do not stop, do not modify
- [ ] `uv` installed and `cd apps/api && uv sync` works
- [ ] `git checkout feat/week-3-4-scaffolding` (branch exists from spec commits)

If any fail, fix or escalate before proceeding.

---

## File Structure

**Backend (`apps/api/`)** — create:
- `app/db/models/base.py` · `app/db/models/{schedule_slot,mood_log,energy_log,explanation,calendar_event,oauth_token,idempotency_key,behavior_event}.py`
- `alembic/versions/0004_migration_hygiene_baseline.py` through `0014_alembic_claim_apscheduler.py`
- `app/middleware/__init__.py` · `app/middleware/{error_envelope,request_id,cors,rate_limit,jwt,idempotency}.py` · `app/middleware/rate_limit.lua`
- `app/events/streams.py` (replaces parts of `publisher.py`; keeps backwards-compat shim)
- `app/calendar/{__init__,oauth,sync,reconcile}.py` · `app/calendar/lock_release.lua`
- `app/crypto/aes_gcm.py`
- `app/jobs/{__init__,scheduler,refresh_tokens,cleanup_idempotency,reaper}.py`
- `app/schemas/{mood,energy,calendar,integrations}.py`
- `app/api/v1/routes/{mood,energy,integrations}.py`
- `scripts/seed_behavior_events.py` · `scripts/dump_openapi.py` · `scripts/dump_schema.py`
- `tests/test_event_spine.py` · `tests/middleware/{test_error_envelope,test_rate_limit,test_jwt,test_idempotency}.py` · `tests/test_calendar_sync.py` · `tests/test_migrations.py`

**Backend** — modify:
- `app/db/models/task.py` (uuid7 default, BaseEntity inheritance, new columns from §2)
- `app/db/models/__init__.py` (register new models)
- `app/api/v1/deps.py` (`get_session_into_request_state`)
- `app/api/v1/routes/tasks.py` (DELETE `/v1/tasks/{id}` route segment)
- `app/api/v1/router.py` (mount new route modules)
- `app/main.py` (middleware registration, scheduler lifespan, streams bootstrap)
- `app/services/task_service.py` (`publish_behavioral` instead of `publish`)
- `app/events/publisher.py` (re-export typed methods from `streams.py`)
- `apps/api/pyproject.toml` (`uuid-utils`, `apscheduler`, `cryptography`, `sse-starlette`)

**Web (`apps/web/`)** — create:
- `src/lib/auth/redirect.ts` · `src/lib/auth/redirect.test.ts`
- `src/lib/sync-status.ts`
- `src/app/(authed)/layout.tsx` · `src/app/(authed)/today/page.tsx` · `src/app/(authed)/schedule/page.tsx` · `src/app/(authed)/settings/layout.tsx` · `src/app/(authed)/settings/page.tsx` · `src/app/(authed)/settings/integrations/page.tsx`
- `src/app/api/tasks/[id]/route.ts`
- `src/components/theme/ThemeToggle.tsx` · `src/components/header/MoodEnergySlot.tsx`
- `src/tests/a11y.test.tsx`

**Web** — modify:
- `src/middleware.ts` (sanitize_next_param wiring, route matchers expand)
- `src/app/layout.tsx` (theme cookie SSR + `Accept-CH` meta)
- `src/app/page.tsx` (route → `/today` for authed, `/login` else)
- `apps/web/package.json` (`@microsoft/fetch-event-source`, `@radix-ui/react-dialog`, `vitest-axe`, `@lhci/cli`, `@axe-core/playwright`)

**UI package (`packages/ui/src/components/`)** — create:
- `sidebar/{index,stories,test}.tsx` · `bottom-tab-nav/{index,stories,test}.tsx` · `floating-action-button/{index,stories,test}.tsx` · `empty-state/{index,stories,test}.tsx` · `banner/{index,stories,test}.tsx` · `skeleton/{index,stories,test}.tsx`

**UI package** — modify:
- `packages/ui/src/index.ts` (re-export new components)

**Events package** — modify:
- `packages/events/README.md` (taxonomy: behavioral vs operational)

**Infra** — create:
- `infra/dev/docker-compose.yml` · `infra/postgres/init/01-timescale.sql` · `infra/grafana/dashboards/event-spine.json`

**Docs** — create:
- `docs/decisions/2026-05-22-local-substrate.md`
- `docs/decisions/2026-05-22-migration-standard.md`
- `docs/decisions/2026-05-22-carry-forward-debt.md`
- `docs/decisions/2026-05-22-calendar-sync.md`
- `docs/decisions/2026-05-22-jwt-bearer-contract.md`
- `docs/decisions/2026-05-22-event-publisher-typing.md`
- `docs/decisions/2026-05-22-onboarding-deferred.md`
- `docs/runbooks/oauth-token-encryption-key-rotation.md`
- `docs/architecture/schema-w3-4.svg` (generated)
- `docs/architecture/explain-snapshots.md`
- `docs/handoffs/week-3-4.md` · `docs/handoffs/week-3-4-smoke-test.md`

**Docs** — modify:
- `docs/CURRENT_SLICE.md` (point to Week 5-6)

**CI** — modify:
- `.github/workflows/pr.yml` (OpenAPI diff gate, Lighthouse CI step)
- `.lighthouserc.json` (new file at repo root)

**Root scripts** — modify:
- `package.json` (`openapi:dump`, `schema:dump`, `lighthouse`)

---

## Commit boundaries (six logical commits, squash-merged)

| Commit | Phases | Covers spec sections |
|---|---|---|
| `feat(week-3-4): postgres schema + migrations` | A · B · C · part of D | §1 substrate · §2 (0004-0010) |
| `feat(week-3-4): timescale hypertable + aggregates` | rest of D | §2 (0011-0013) + seed |
| `feat(week-3-4): event spine` | E | §3 |
| `feat(week-3-4): api middleware + stub endpoints` | G · H | §4 |
| `feat(week-3-4): google calendar oauth + polling sync` | I · J · K | §5 (+ migration 0014) |
| `feat(week-3-4): frontend shell` | F · L · M | §6 + §7 handoff artifacts |

---

# Phase A — Substrate (Day 1)

## Task 1: Docker compose for pg16+timescale and redis

**Files:**
- Create: `infra/dev/docker-compose.yml`
- Create: `infra/postgres/init/01-timescale.sql`
- Modify: `apps/api/.env.example` · root `.env.example` if present

- [ ] **Step 1: Write `infra/postgres/init/01-timescale.sql`**

```sql
-- Loaded once on container init via /docker-entrypoint-initdb.d.
-- Idempotent so re-init or post-restore is safe.
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
-- gen_random_uuid() is core in PG13+; no pgcrypto required.
```

- [ ] **Step 2: Write `infra/dev/docker-compose.yml`**

```yaml
services:
  postgres:
    image: timescale/timescaledb:2.17.2-pg16
    container_name: lockin-postgres
    command:
      - postgres
      - -c
      - shared_preload_libraries=timescaledb
    environment:
      POSTGRES_USER: lockin
      POSTGRES_PASSWORD: lockin
      POSTGRES_DB: lockin_dev
      TIMESCALEDB_TELEMETRY: "off"
    ports:
      - "5433:5432"
    volumes:
      - lockin-pg-data:/var/lib/postgresql/data
      - ../postgres/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "lockin", "-d", "lockin_dev"]
      interval: 5s
      timeout: 3s
      retries: 10

  redis:
    image: redis:7.4-alpine
    container_name: lockin-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  lockin-pg-data:
```

- [ ] **Step 3: Boot the stack and verify the extension loads**

```bash
docker compose -f infra/dev/docker-compose.yml up -d
docker exec lockin-postgres psql -U lockin -d lockin_dev -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';"
```
Expected: one row, `timescaledb | 2.17.2`.

- [ ] **Step 4: Update `apps/api/.env.example` DATABASE_URL**

Change the existing `DATABASE_URL=` line to:
```
DATABASE_URL=postgresql+asyncpg://lockin:lockin@localhost:5433/lockin_dev
DATABASE_URL_SYNC=postgresql://lockin:lockin@localhost:5433/lockin_dev
DATABASE_URL_TEST=postgresql+asyncpg://lockin:lockin@localhost:5433/lockin_test
```

- [ ] **Step 5: Create the test database**

```bash
docker exec lockin-postgres psql -U lockin -d lockin_dev -c "CREATE DATABASE lockin_test;"
docker exec lockin-postgres psql -U lockin -d lockin_test -c "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"
```

- [ ] **Step 6: Commit**

```bash
git add infra/dev/docker-compose.yml infra/postgres/init/01-timescale.sql apps/api/.env.example
git commit -m "infra(dev): pg16+timescale on :5433, redis on :6379, init script + healthchecks"
```

## Task 2: Substrate decision log

**Files:**
- Create: `docs/decisions/2026-05-22-local-substrate.md`

- [ ] **Step 1: Write the decision log**

```markdown
# Local dev substrate: Docker pg16+timescale on :5433

**Date:** 2026-05-22
**Status:** Accepted
**Slice:** Week 3-4 Scaffolding

## Context
Week 3-4 needs TimescaleDB hypertables. The host machine runs native
PostgreSQL 18 bound to :5432 (per Slice 0 environment notes), and that
instance does not have the timescaledb extension. CLAUDE.md locks the
production stack at PG16.

## Decision
Run `timescale/timescaledb:2.17.2-pg16` in Docker, publish to host
:5433. Pinned tag, not `latest`. The container runs with
`shared_preload_libraries=timescaledb` and `TIMESCALEDB_TELEMETRY=off`.
An init script at `infra/postgres/init/01-timescale.sql` creates the
extension on first boot.

The native PG18 instance is left untouched and is not used by LockIn
for any purpose.

## Consequences
- `DATABASE_URL` for LockIn always points at :5433.
- Developers do not need to stop/start native PG.
- `gen_random_uuid()` works without `pgcrypto` (PG13+ core builtin).
- Migration `0001` (TimescaleDB hypertable) now applies for real;
  the previous `alembic stamp 0001` workaround is no longer needed.
```

- [ ] **Step 2: Commit**

```bash
git add docs/decisions/2026-05-22-local-substrate.md
git commit -m "docs(decisions): local dev substrate uses dockerized pg16+timescale on :5433"
```

## Task 3: Apply migration 0001 against the real substrate

Migration 0001 (TimescaleDB hypertable from Week 1-2) was `alembic stamp`'d past on the native PG. With the extension loaded, it must run for real.

- [ ] **Step 1: Drop and recreate dev DB to reset alembic history**

```bash
docker exec lockin-postgres psql -U lockin -d postgres -c "DROP DATABASE lockin_dev;"
docker exec lockin-postgres psql -U lockin -d postgres -c "CREATE DATABASE lockin_dev;"
docker exec lockin-postgres psql -U lockin -d lockin_dev -c "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"
```

- [ ] **Step 2: Run alembic upgrade from zero**

```bash
cd apps/api
uv run alembic upgrade head
```
Expected: migrations `0001`, `0002`, `0003` all apply successfully. The `behavior_events` hypertable from `0001` registers in `_timescaledb_catalog.hypertable`.

- [ ] **Step 3: Verify hypertable**

```bash
docker exec lockin-postgres psql -U lockin -d lockin_dev -c "SELECT * FROM timescaledb_information.hypertables;"
```
Expected: one row for `behavior_events`.

- [ ] **Step 4: Verify downgrade-upgrade idempotency**

```bash
cd apps/api
uv run alembic downgrade base
uv run alembic upgrade head
```
Expected: both succeed, no errors.

- [ ] **Step 5: Run existing test suite against new substrate**

```bash
cd apps/api
uv run pytest -q
```
Expected: all Slice 0 tests pass against `:5433`.

- [ ] **Step 6: Commit (no code change — verification only)**

No commit needed; this task is verification. If `apps/api/uv.lock` updated, commit it:
```bash
git add apps/api/uv.lock 2>/dev/null || true
git diff --cached --quiet || git commit -m "chore(api): refresh uv.lock against new substrate"
```

## Task 4: Add `uuid-utils` dependency

**Files:**
- Modify: `apps/api/pyproject.toml`
- Modify: `apps/api/uv.lock` (regenerated)

- [ ] **Step 1: Add to `[project] dependencies` in `apps/api/pyproject.toml`**

Find the existing `dependencies = [...]` list and insert:
```toml
    "uuid-utils==0.10.0",
```
(Use the latest 0.x release at write-time. Pin exact, not `^` or `~=`.)

- [ ] **Step 2: Sync**

```bash
cd apps/api
uv sync
```

- [ ] **Step 3: Smoke-test the import**

```bash
cd apps/api
uv run python -c "import uuid_utils; u = uuid_utils.uuid7(); print(u, len(str(u)))"
```
Expected: prints a UUID and `36`.

- [ ] **Step 4: Commit**

```bash
git add apps/api/pyproject.toml apps/api/uv.lock
git commit -m "deps(api): add uuid-utils==0.10.0 (Rust-backed UUIDv7 generator)"
```

## Task 5: `BaseEntity` + `UUIDv7Mixin` model mixins

**Files:**
- Create: `apps/api/app/db/models/base.py`

This file is the standard-row-shape contract for §2. Every new model in this slice inherits from it.

- [ ] **Step 1: Write the mixins**

```python
"""Shared SQLAlchemy mixins for the standard row shape (Week 3-4 §2)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import uuid_utils
from sqlalchemy import BigInteger, DateTime, Integer, SmallInteger, func, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


def _uuid7() -> UUID:
    """UUID v7 generator — time-ordered, used as ORM default on hot tables."""
    return UUID(str(uuid_utils.uuid7()))


class BaseEntityMixin:
    """Standard row shape from spec §2.

    Every domain table in Week 3-4 inherits this. `id` defaults to v4 at the
    server (raw-SQL fallback); hot-table subclasses override the ORM default
    to uuid7 via UUIDv7Mixin so writes from Python are time-ordered.
    """

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    tenant_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer, server_default=text("1"), nullable=False
    )


class UUIDv7Mixin:
    """Hot-table override: ORM-side uuid7 default. Server still has v4 fallback."""

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=_uuid7,
        server_default=text("gen_random_uuid()"),
    )
```

- [ ] **Step 2: Smoke-test the import**

```bash
cd apps/api
uv run python -c "from app.db.models.base import BaseEntityMixin, UUIDv7Mixin, _uuid7; print(_uuid7())"
```
Expected: prints a UUID.

- [ ] **Step 3: Commit**

```bash
git add apps/api/app/db/models/base.py
git commit -m "feat(api): BaseEntityMixin + UUIDv7Mixin for the standard row shape"
```

---

# Phase B — Migration baseline + tasks expansion (Day 1)

## Task 6: Migration `0004` — hygiene baseline (back-fix)

**Files:**
- Create: `apps/api/alembic/versions/0004_migration_hygiene_baseline.py`
- Modify: `apps/api/app/db/models/task.py`

This migration is the **server-side half** of the v4-fallback pattern; the matching ORM edit (Task model gains `default=_uuid7`) lands in the same commit. v4 server default is the safety net for raw SQL, not the truth — `tasks` rows from the app are v7.

- [ ] **Step 1: Write the migration**

```python
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
    op.execute(
        "ALTER TABLE webauthn_credentials "
        "ALTER COLUMN id SET DEFAULT gen_random_uuid()"
    )

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
```

- [ ] **Step 2: Flip `tasks.id` ORM default to v7**

Edit `apps/api/app/db/models/task.py`. Change:
```python
from uuid import UUID, uuid4
...
id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
```
To:
```python
from uuid import UUID

from app.db.models.base import _uuid7
...
id: Mapped[UUID] = mapped_column(
    PgUUID(as_uuid=True),
    primary_key=True,
    default=_uuid7,
    server_default=sa.text("gen_random_uuid()"),
)
```
(Add `import sqlalchemy as sa` at module top if not present.)

- [ ] **Step 3: Run alembic up + down + up**

```bash
cd apps/api
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
```
Expected: all three succeed; final state has 0004 applied.

- [ ] **Step 4: Verify the composite index is used**

```bash
docker exec lockin-postgres psql -U lockin -d lockin_dev -c \
  "EXPLAIN ANALYZE SELECT * FROM tasks WHERE user_id = '00000000-0000-0000-0000-000000000000' ORDER BY created_at DESC, id DESC LIMIT 20;"
```
Expected: `Index Scan using ix_tasks_user_id_created_at`.

- [ ] **Step 5: Run existing Slice 0 task tests**

```bash
cd apps/api
uv run pytest tests/ -q -k task
```
Expected: green. uuid7 ORM default does not break existing tests.

- [ ] **Step 6: Commit**

```bash
git add apps/api/alembic/versions/0004_migration_hygiene_baseline.py apps/api/app/db/models/task.py
git commit -m "feat(api): migration 0004 hygiene baseline + tasks.id flips to uuid7"
```

## Task 7: Migration standard decision log

**Files:**
- Create: `docs/decisions/2026-05-22-migration-standard.md`

- [ ] **Step 1: Write the decision log**

```markdown
# Migration standard for Week 3-4 onward

**Date:** 2026-05-22
**Status:** Accepted

## Standard row shape
Every domain table created from migration 0004 onward carries:
- `id UUID PRIMARY KEY DEFAULT gen_random_uuid()` (v4 server fallback)
- `user_id UUID NOT NULL`
- `tenant_id UUID NULL`, indexed (forward-compat for P2 team mode)
- `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`
- `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` (ORM `onupdate=func.now()`)
- `version INT NOT NULL DEFAULT 1` (optimistic concurrency)

## UUID strategy (hybrid)
**Hot tables** (`behavior_events`, `tasks`, `mood_logs`, `energy_logs`) use
ORM default `uuid_utils.uuid7()` for time-ordering / B-tree locality.
**Cold tables** rely on the server v4 default.

Both groups carry the v4 `server_default` as a safety net for raw SQL.
Hand-rolled v7 bit-packing is prohibited — only `uuid_utils` (Rust/PyO3,
pinned exact version).

## Index pattern
List queries are always `WHERE user_id = $1 ORDER BY <ts_col> DESC`. The
standard composite is `(user_id, <ts_col> DESC, id DESC)` — id is the
monotonic tiebreaker preventing flake when two rows share a timestamp.

## Optimistic concurrency
Mutations that update existing rows must use `WHERE id = $1 AND version = $2`
and `SET version = version + 1`. P1 does not enforce this in middleware;
services that need it call it explicitly. This is scaffolding, not a contract.
```

- [ ] **Step 2: Commit**

```bash
git add docs/decisions/2026-05-22-migration-standard.md
git commit -m "docs(decisions): migration + UUID + index standard for Week 3-4 onward"
```

## Task 8: Migration `0005` — task expansion

**Files:**
- Create: `apps/api/alembic/versions/0005_tasks_expansion.py`
- Modify: `apps/api/app/db/models/task.py`

- [ ] **Step 1: Write the migration**

```python
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
    op.add_column("tasks", sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False))
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
    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")
    op.drop_constraint("ck_tasks_status", "tasks", type_="check")
    op.drop_column("tasks", "status")
    op.drop_column("tasks", "version")
    op.drop_column("tasks", "updated_at")
    op.drop_index("ix_tasks_tenant_id", table_name="tasks")
    op.drop_column("tasks", "tenant_id")
```

- [ ] **Step 2: Extend the `Task` model**

Edit `apps/api/app/db/models/task.py` to add the four new columns alongside existing ones:
```python
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import DateTime, Integer, String, func, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.base import _uuid7


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=_uuid7,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    tenant_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False, server_default="keyboard")
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="captured")
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

- [ ] **Step 3: Run migrations**

```bash
cd apps/api
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
```

- [ ] **Step 4: Run existing tests**

```bash
cd apps/api
uv run pytest tests/ -q -k task
```
Expected: green. `status` and `version` default at insert time.

- [ ] **Step 5: Commit**

```bash
git add apps/api/alembic/versions/0005_tasks_expansion.py apps/api/app/db/models/task.py
git commit -m "feat(api): tasks expansion (tenant_id, updated_at trigger, version, status)"
```

## Task 9: Migration test scaffolding

**Files:**
- Create: `apps/api/tests/test_migrations.py`

A single test that asserts the full alembic chain is reversible. Fails immediately if a future migration breaks downgrade.

- [ ] **Step 1: Write the test**

```python
"""Asserts every migration in the chain can downgrade and re-upgrade cleanly."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

API_DIR = Path(__file__).resolve().parents[1]


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "alembic", *args],
        cwd=API_DIR,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.integration
def test_alembic_chain_is_reversible() -> None:
    head = _alembic("upgrade", "head")
    assert head.returncode == 0, head.stderr
    base = _alembic("downgrade", "base")
    assert base.returncode == 0, base.stderr
    head2 = _alembic("upgrade", "head")
    assert head2.returncode == 0, head2.stderr
```

- [ ] **Step 2: Mark `integration` in pytest config**

If `apps/api/pyproject.toml` doesn't already register the marker, add to `[tool.pytest.ini_options]`:
```toml
markers = ["integration: marks tests that require docker compose services"]
```

- [ ] **Step 3: Run the test**

```bash
cd apps/api
uv run pytest tests/test_migrations.py -v
```
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/api/tests/test_migrations.py apps/api/pyproject.toml
git commit -m "test(api): assert alembic chain is fully reversible"
```

---

# Phase C — Domain tables (Day 2)

Each task in this phase follows the same shape: model → migration → register in `__init__` → run upgrade/downgrade → commit. The first task (Task 10) shows the full step list; subsequent tasks abbreviate where the pattern repeats verbatim.

## Task 10: `schedule_slots` table (migration 0006)

**Files:**
- Create: `apps/api/app/db/models/schedule_slot.py`
- Create: `apps/api/alembic/versions/0006_schedule_slots.py`
- Modify: `apps/api/app/db/models/__init__.py`

- [ ] **Step 1: Write the SQLAlchemy model**

```python
"""ScheduleSlot — a time-window allocation for a Task. Spec §2 migration 0006."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.base import BaseEntityMixin


class ScheduleSlot(BaseEntityMixin, Base):
    __tablename__ = "schedule_slots"

    task_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False)
```

- [ ] **Step 2: Write the migration**

```python
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
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("task_id", UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.SmallInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
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
```

- [ ] **Step 3: Register the model**

Edit `apps/api/app/db/models/__init__.py` and add:
```python
from app.db.models.schedule_slot import ScheduleSlot  # noqa: F401
```

- [ ] **Step 4: Run migrations and the chain test**

```bash
cd apps/api
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
uv run pytest tests/test_migrations.py -v
```

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/db/models/schedule_slot.py apps/api/alembic/versions/0006_schedule_slots.py apps/api/app/db/models/__init__.py
git commit -m "feat(api): schedule_slots table (migration 0006)"
```

## Task 11: `mood_logs` table (migration 0007)

**Files:**
- Create: `apps/api/app/db/models/mood_log.py`
- Create: `apps/api/alembic/versions/0007_mood_logs.py`
- Modify: `apps/api/app/db/models/__init__.py`

- [ ] **Step 1: Write the model (hot table — uses `UUIDv7Mixin`)**

```python
"""MoodLog — a user-reported mood score. Spec §2 migration 0007. Hot table (v7 ORM)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, SmallInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.base import BaseEntityMixin, UUIDv7Mixin


class MoodLog(UUIDv7Mixin, BaseEntityMixin, Base):
    __tablename__ = "mood_logs"
    __table_args__ = (CheckConstraint("score BETWEEN 1 AND 5", name="ck_mood_logs_score"),)

    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
```

- [ ] **Step 2: Write the migration**

```python
"""0007 mood_logs."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mood_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("logged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.SmallInteger(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("score BETWEEN 1 AND 5", name="ck_mood_logs_score"),
    )
    op.create_index("ix_mood_logs_tenant_id", "mood_logs", ["tenant_id"])
    op.create_index(
        "ix_mood_logs_user_id_logged_at",
        "mood_logs",
        ["user_id", sa.text("logged_at DESC"), sa.text("id DESC")],
    )
    op.execute(
        "CREATE TRIGGER mood_logs_set_updated_at BEFORE UPDATE ON mood_logs "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS mood_logs_set_updated_at ON mood_logs;")
    op.drop_index("ix_mood_logs_user_id_logged_at", table_name="mood_logs")
    op.drop_index("ix_mood_logs_tenant_id", table_name="mood_logs")
    op.drop_table("mood_logs")
```

- [ ] **Step 3: Register, migrate, verify, commit** (same pattern as Task 10 step 3-5; commit message `feat(api): mood_logs table (migration 0007)`)

## Task 12: `energy_logs` table (migration 0008)

Identical shape to `mood_logs` — same hot-table mixin, same index, same score check.

**Files:**
- Create: `apps/api/app/db/models/energy_log.py` (copy of `mood_log.py` with class/table renamed; constraint becomes `ck_energy_logs_score`)
- Create: `apps/api/alembic/versions/0008_energy_logs.py` (copy of `0007` with table/constraint/index/trigger names changed)

- [ ] **Step 1-5: Follow Task 11 pattern exactly**, substituting `mood_logs → energy_logs`, `MoodLog → EnergyLog`, `score` constraint name to `ck_energy_logs_score`. Commit message: `feat(api): energy_logs table (migration 0008)`.

## Task 13: `explanations` table (migration 0009)

**Files:**
- Create: `apps/api/app/db/models/explanation.py`
- Create: `apps/api/alembic/versions/0009_explanations.py`

- [ ] **Step 1: Model (cold table — no UUIDv7Mixin)**

```python
"""Explanation — structured reasoning for a scheduling/agent decision. Spec §2 migration 0009."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.base import BaseEntityMixin


class Explanation(BaseEntityMixin, Base):
    __tablename__ = "explanations"

    subject_type: Mapped[str] = mapped_column(String(32), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    reasoning: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
```

- [ ] **Step 2: Migration body** — standard cols + `subject_type VARCHAR(32) NOT NULL`, `subject_id UUID NOT NULL`, `reasoning JSONB NOT NULL`, `model_id VARCHAR(64) NOT NULL`, `latency_ms INT NOT NULL`. Index `(user_id, created_at DESC, id DESC)`. Trigger same shape. Use `0010` task's migration as a template.

- [ ] **Step 3-5: Register, migrate, commit.** Commit message: `feat(api): explanations table (migration 0009)`.

## Task 14: `calendar_events` table (migration 0010)

**Files:**
- Create: `apps/api/app/db/models/calendar_event.py`
- Create: `apps/api/alembic/versions/0010_calendar_events.py`

- [ ] **Step 1: Model (cold table)**

```python
"""CalendarEvent — Google Calendar event ingested via read-only sync. Spec §2 migration 0010."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.base import BaseEntityMixin


class CalendarEvent(BaseEntityMixin, Base):
    __tablename__ = "calendar_events"
    __table_args__ = (UniqueConstraint("user_id", "google_event_id", name="uq_calendar_events_user_google_id"),)

    google_event_id: Mapped[str] = mapped_column(String(1024), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    etag: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_calendar_id: Mapped[str] = mapped_column(String(256), nullable=False, server_default="primary")
```

- [ ] **Step 2: Migration body** — standard cols + the above. Unique on `(user_id, google_event_id)`. Index `(user_id, starts_at)`. Trigger.

- [ ] **Step 3-5: Register, migrate, commit.** Commit message: `feat(api): calendar_events table (migration 0010)`.

---

# Phase D — Infra tables, Timescale, seed (Day 3)

## Task 15: AES-GCM crypto module (used by Task 16)

**Files:**
- Create: `apps/api/app/crypto/__init__.py`
- Create: `apps/api/app/crypto/aes_gcm.py`
- Create: `apps/api/tests/test_crypto.py`
- Modify: `apps/api/pyproject.toml` (add `cryptography`)

- [ ] **Step 1: Add `cryptography` dep**

In `apps/api/pyproject.toml` dependencies list:
```toml
    "cryptography==43.0.3",
```
Then `cd apps/api && uv sync`.

- [ ] **Step 2: Write the failing test first**

Create `apps/api/tests/test_crypto.py`:
```python
"""AES-GCM envelope encryption with versioned keys (spec §5)."""

from __future__ import annotations

import os

import pytest

from app.crypto.aes_gcm import EnvelopeCipher, KeyVersion


@pytest.fixture
def cipher(monkeypatch: pytest.MonkeyPatch) -> EnvelopeCipher:
    # 32-byte keys; v1 + v2 simulating a rotation in progress.
    monkeypatch.setenv("OAUTH_TOKEN_ENCRYPTION_KEY_V1", os.urandom(32).hex())
    monkeypatch.setenv("OAUTH_TOKEN_ENCRYPTION_KEY_V2", os.urandom(32).hex())
    return EnvelopeCipher.from_env(prefix="OAUTH_TOKEN_ENCRYPTION_KEY")


def test_encrypts_with_highest_version_and_round_trips(cipher: EnvelopeCipher) -> None:
    blob, version = cipher.encrypt(b"hello refresh token")
    assert version == KeyVersion(2)
    assert cipher.decrypt(blob, version) == b"hello refresh token"


def test_decrypts_legacy_version_after_rotation(cipher: EnvelopeCipher) -> None:
    blob_v1, _ = cipher.encrypt_with_version(b"old row", KeyVersion(1))
    assert cipher.decrypt(blob_v1, KeyVersion(1)) == b"old row"


def test_rejects_missing_version(cipher: EnvelopeCipher) -> None:
    with pytest.raises(KeyError):
        cipher.decrypt(b"garbage", KeyVersion(99))
```

Run: `cd apps/api && uv run pytest tests/test_crypto.py -v` → FAIL with `ModuleNotFoundError: app.crypto`.

- [ ] **Step 3: Implement the module**

`apps/api/app/crypto/__init__.py`:
```python
from app.crypto.aes_gcm import EnvelopeCipher, KeyVersion

__all__ = ["EnvelopeCipher", "KeyVersion"]
```

`apps/api/app/crypto/aes_gcm.py`:
```python
"""AES-GCM envelope encryption with versioned keys.

Used for at-rest encryption of OAuth refresh tokens (spec §5).
Rotation pattern documented in docs/runbooks/oauth-token-encryption-key-rotation.md.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import NewType

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KeyVersion = NewType("KeyVersion", int)


@dataclass(frozen=True)
class EnvelopeCipher:
    """Holds N AES-GCM keys keyed by version; encrypts with the highest."""

    keys: dict[KeyVersion, bytes]

    @classmethod
    def from_env(cls, *, prefix: str) -> "EnvelopeCipher":
        keys: dict[KeyVersion, bytes] = {}
        for name, value in os.environ.items():
            if not name.startswith(f"{prefix}_V"):
                continue
            try:
                version = KeyVersion(int(name.removeprefix(f"{prefix}_V")))
            except ValueError:
                continue
            raw = bytes.fromhex(value)
            if len(raw) != 32:
                raise ValueError(f"{name} must be 32 bytes hex (AES-256)")
            keys[version] = raw
        if not keys:
            raise RuntimeError(f"No {prefix}_V<n> env vars defined")
        return cls(keys=keys)

    @property
    def current_version(self) -> KeyVersion:
        return max(self.keys)

    def encrypt(self, plaintext: bytes) -> tuple[bytes, KeyVersion]:
        return self.encrypt_with_version(plaintext, self.current_version)

    def encrypt_with_version(self, plaintext: bytes, version: KeyVersion) -> tuple[bytes, KeyVersion]:
        if version not in self.keys:
            raise KeyError(version)
        nonce = os.urandom(12)
        ciphertext = AESGCM(self.keys[version]).encrypt(nonce, plaintext, None)
        return nonce + ciphertext, version

    def decrypt(self, blob: bytes, version: KeyVersion) -> bytes:
        if version not in self.keys:
            raise KeyError(version)
        nonce, ciphertext = blob[:12], blob[12:]
        return AESGCM(self.keys[version]).decrypt(nonce, ciphertext, None)
```

- [ ] **Step 4: Run tests**

```bash
cd apps/api
uv run pytest tests/test_crypto.py -v
```
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/crypto/ apps/api/tests/test_crypto.py apps/api/pyproject.toml apps/api/uv.lock
git commit -m "feat(api): AES-GCM envelope encryption with versioned keys"
```

## Task 16: `oauth_tokens` table (migration 0011)

**Files:**
- Create: `apps/api/app/db/models/oauth_token.py`
- Create: `apps/api/alembic/versions/0011_oauth_tokens.py`

- [ ] **Step 1: Model**

```python
"""OAuthToken — per-(user, provider) refresh/access tokens, AES-GCM encrypted. Spec §5."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    ARRAY,
    DateTime,
    Integer,
    LargeBinary,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.base import BaseEntityMixin


class OAuthToken(BaseEntityMixin, Base):
    __tablename__ = "oauth_tokens"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_oauth_tokens_user_provider"),)

    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    refresh_token_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    access_token_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    key_version: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="1", index=True)
    access_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    granted_scopes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default="{}")
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refresh_failure_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    sync_token: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    calendar_initial_sync_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
```

- [ ] **Step 2: Migration** — standard cols + the columns above + unique constraint + index on `key_version` + trigger. Use the Task 11 migration body as template.

- [ ] **Step 3-5: Register, migrate, commit.** Commit message: `feat(api): oauth_tokens table with versioned envelope encryption (migration 0011)`.

## Task 17: `idempotency_keys` table (migration 0012)

**Files:**
- Create: `apps/api/app/db/models/idempotency_key.py`
- Create: `apps/api/alembic/versions/0012_idempotency_keys.py`

- [ ] **Step 1: Model**

```python
"""IdempotencyKey — middleware-cached response for replay. Spec §4."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    LargeBinary,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from typing import Any

from app.db.base import Base
from app.db.models.base import BaseEntityMixin


class IdempotencyKey(BaseEntityMixin, Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (UniqueConstraint("user_id", "client_idempotency_key", name="uq_idempotency_user_key"),)

    client_idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    response_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status_code: Mapped[int] = mapped_column(SmallInteger, nullable=False)
```

- [ ] **Step 2: Migration body** — standard cols + above. Two indexes: `UNIQUE (user_id, client_idempotency_key)` and `INDEX (created_at)` (born-with the table per §4 bend #5).

- [ ] **Step 3-5: Register, migrate, commit.** Commit message: `feat(api): idempotency_keys table + created_at index (migration 0012)`.

## Task 18: `behavior_events` hypertable + continuous aggregates (migration 0013)

**Files:**
- Create: `apps/api/app/db/models/behavior_event.py`
- Create: `apps/api/alembic/versions/0013_behavior_events_hypertable.py`

This task uses raw SQL exclusively for the TimescaleDB-specific operations because Alembic's autogenerate cannot model them.

- [ ] **Step 1: Model (hot table; written via SQLAlchemy for read paths)**

```python
"""BehaviorEvent — TimescaleDB hypertable for behavioral events. Spec §2 migration 0013."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.base import UUIDv7Mixin


class BehaviorEvent(UUIDv7Mixin, Base):
    __tablename__ = "behavior_events"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
```

Note: This intentionally does NOT inherit `BaseEntityMixin` (no `updated_at`/`version` on append-only events; only `id`, `user_id`, `created_at`).

- [ ] **Step 2: Migration**

```python
"""0013 behavior_events hypertable + continuous aggregates."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "behavior_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.execute(
        "SELECT create_hypertable('behavior_events', 'occurred_at', "
        "chunk_time_interval => INTERVAL '1 month');"
    )
    op.create_index(
        "ix_behavior_events_user_type_occurred",
        "behavior_events",
        ["user_id", "event_type", sa.text("occurred_at DESC")],
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
    # Retention policy commented, not registered (spec §2).
    op.execute(
        "-- Retention policy: raw events 90d, aggregates indefinite. "
        "Documented; not registered for P1. See spec §2."
    )


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS daily_mood_avg CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS daily_task_completions CASCADE;")
    op.execute("SELECT remove_compression_policy('behavior_events', if_exists => true);")
    op.drop_index("ix_behavior_events_user_type_occurred", table_name="behavior_events")
    op.drop_table("behavior_events")
```

Note: this REPLACES the W1-2 migration `0001` table — `0001` already created a `behavior_events` hypertable. If `0001` did so with the same shape, drop it from the chain or rename the table here. **Verify before merging:**

```bash
docker exec lockin-postgres psql -U lockin -d lockin_dev -c "\d behavior_events"
```
If the W1-2 table exists with a different shape, replace migration `0001`'s upgrade body with a no-op (leave it as a chain anchor) and add a guard `DROP TABLE IF EXISTS behavior_events CASCADE` at the top of `0013.upgrade()`. Document in the migration docstring why.

- [ ] **Step 3: Register, migrate, verify aggregates exist**

```bash
cd apps/api
uv run alembic upgrade head
docker exec lockin-postgres psql -U lockin -d lockin_dev -c "SELECT view_name FROM timescaledb_information.continuous_aggregates;"
```
Expected: 2 rows, `daily_task_completions` and `daily_mood_avg`.

- [ ] **Step 4: Commit**

```bash
git add apps/api/app/db/models/behavior_event.py apps/api/alembic/versions/0013_behavior_events_hypertable.py apps/api/app/db/models/__init__.py
git commit -m "feat(api): behavior_events hypertable + 2 continuous aggregates (migration 0013)"
```

## Task 19: Seed script for 1M behavior events + Timescale validation test

**Files:**
- Create: `apps/api/scripts/seed_behavior_events.py`
- Create: `apps/api/tests/test_timescale_perf.py`

- [ ] **Step 1: Write the seed script**

```python
"""Generate 1M synthetic behavior_events across 10 users x 90 days.

Used to validate that the continuous aggregate query stays <100ms after refresh
and that compression engages on backdated chunks. Spec §2 acceptance criteria.

Usage: uv run python scripts/seed_behavior_events.py
"""

from __future__ import annotations

import asyncio
import json
import random
from datetime import datetime, timedelta, timezone
from uuid import UUID

import uuid_utils
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

USERS = [UUID(str(uuid_utils.uuid7())) for _ in range(10)]
EVENT_TYPES = ["task.created", "task.completed", "mood.logged", "energy.logged"]
BATCH_SIZE = 5000
TOTAL_EVENTS = 1_000_000


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    start = datetime.now(timezone.utc) - timedelta(days=90)
    rows_remaining = TOTAL_EVENTS

    async with engine.begin() as conn:
        await conn.exec_driver_sql("TRUNCATE behavior_events;")

    batch: list[tuple[str, str, str, str, str]] = []
    inserted = 0
    while rows_remaining > 0:
        n = min(BATCH_SIZE, rows_remaining)
        for _ in range(n):
            user = random.choice(USERS)
            event_type = random.choice(EVENT_TYPES)
            offset_seconds = random.randint(0, 90 * 86400)
            occurred_at = start + timedelta(seconds=offset_seconds)
            payload = {"score": random.randint(1, 5)} if event_type == "mood.logged" else {}
            batch.append(
                (
                    str(uuid_utils.uuid7()),
                    str(user),
                    event_type,
                    occurred_at.isoformat(),
                    json.dumps(payload),
                )
            )
        async with engine.begin() as conn:
            await conn.exec_driver_sql(
                "INSERT INTO behavior_events (id, user_id, event_type, occurred_at, payload) "
                "VALUES " + ",".join(["(%s, %s, %s, %s, %s)"] * len(batch)),
                tuple(v for row in batch for v in row),
            )
        inserted += len(batch)
        rows_remaining -= len(batch)
        batch.clear()
        print(f"  inserted {inserted:>9,}/{TOTAL_EVENTS:,}")

    async with engine.begin() as conn:
        await conn.exec_driver_sql("CALL refresh_continuous_aggregate('daily_task_completions', NULL, NULL);")
        await conn.exec_driver_sql("CALL refresh_continuous_aggregate('daily_mood_avg', NULL, NULL);")
    print("Aggregates refreshed.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Run the seed**

```bash
cd apps/api
uv run python scripts/seed_behavior_events.py
```
Expected: ~2-3 minute runtime, ends with "Aggregates refreshed."

- [ ] **Step 3: Write the perf test**

```python
"""Validates Timescale aggregate query latency and compression engagement.

Requires the seed script to have been run; if rows < 100k the test xfails.
"""

from __future__ import annotations

import time

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


@pytest.mark.integration
@pytest.mark.asyncio
async def test_aggregate_query_under_100ms() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        count_row = await conn.execute(text("SELECT count(*) FROM behavior_events"))
        if count_row.scalar_one() < 100_000:
            pytest.xfail("Seed script not run; <100k rows in behavior_events")

        # Cold query to warm OS page cache.
        await conn.execute(
            text(
                "SELECT user_id, sum(completions) FROM daily_task_completions "
                "WHERE day > now() - interval '30 days' GROUP BY user_id"
            )
        )

        start = time.perf_counter()
        await conn.execute(
            text(
                "SELECT user_id, sum(completions) FROM daily_task_completions "
                "WHERE day > now() - interval '30 days' GROUP BY user_id"
            )
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 100, f"aggregate query took {elapsed_ms:.1f}ms"
    await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_compression_engages_on_backdated_chunk() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        chunks = await conn.execute(
            text(
                "SELECT chunk_schema || '.' || chunk_name AS chunk "
                "FROM timescaledb_information.chunks "
                "WHERE hypertable_name = 'behavior_events' "
                "AND range_end < now() - interval '7 days' "
                "ORDER BY range_end LIMIT 1"
            )
        )
        row = chunks.fetchone()
        if row is None:
            pytest.xfail("No backdated chunks; seed older data or extend script window")
        # Force compression (policy is async).
        await conn.execute(text(f"SELECT compress_chunk('{row.chunk}')"))
        check = await conn.execute(
            text("SELECT is_compressed FROM timescaledb_information.chunks WHERE chunk_name = :n"),
            {"n": row.chunk.split(".")[-1]},
        )
        assert check.scalar_one() is True
    await engine.dispose()
```

- [ ] **Step 4: Run perf tests**

```bash
cd apps/api
uv run pytest tests/test_timescale_perf.py -v
```
Expected: both PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/scripts/seed_behavior_events.py apps/api/tests/test_timescale_perf.py
git commit -m "test(api): 1M-event seed + aggregate latency + compression engagement"
```

---

# Phase E — Event spine (Day 4-5)

## Task 20: Event publisher typing decision log + taxonomy

**Files:**
- Create: `docs/decisions/2026-05-22-event-publisher-typing.md`
- Modify: `packages/events/README.md`

- [ ] **Step 1: Write the decision log**

```markdown
# Event publisher typing: behavioral vs operational at the API surface

**Date:** 2026-05-22
**Status:** Accepted

## Decision
`EventPublisher` exposes two methods, not one:
- `publish_behavioral(event)` — writes to the Redis Stream AND (Week 5+)
  the consumer enqueues a `behavior_events` hypertable insert.
- `publish_operational(event)` — writes to the Redis Stream only. Never
  pollutes the behavior graph.

Callers MUST pick the typed method at the call site. There is no generic
`publish(event)`.

## Why
Calendar events from Google are ingested data, not user actions; routing
them into `behavior_events` would corrupt the long-tail behavioral dataset
that is the product's moat. Comment-only conventions don't survive review
churn. Enforcing the distinction at the API surface makes accidental
mis-routing impossible at compile time (in spirit; Python is dynamic, but
mypy + ruff catch it).

## Taxonomy
**Behavioral:** `task.created, task.completed, task.scheduled, task.accepted,
task.rejected, task.modified, mood.logged, energy.logged`
**Operational:** `calendar.connected, calendar.event_synced, calendar.disconnected,
agent.action_proposed, agent.action_committed, system.*`
```

- [ ] **Step 2: Append taxonomy to `packages/events/README.md`**

Add a new section at the bottom:
```markdown
## Behavioral vs operational events

Events are split at the publisher API surface (`publish_behavioral` vs
`publish_operational`). See `docs/decisions/2026-05-22-event-publisher-typing.md`.

| Category | Event types |
|---|---|
| Behavioral (feeds `behavior_events` hypertable) | `task.created`, `task.completed`, `task.scheduled`, `task.accepted`, `task.rejected`, `task.modified`, `mood.logged`, `energy.logged` |
| Operational (stream-only) | `calendar.connected`, `calendar.event_synced`, `calendar.disconnected`, `agent.action_proposed`, `agent.action_committed`, `system.*` |
```

- [ ] **Step 3: Commit**

```bash
git add docs/decisions/2026-05-22-event-publisher-typing.md packages/events/README.md
git commit -m "docs(events): behavioral vs operational publisher typing decision + taxonomy"
```

## Task 21: `EventPublisher` refactor + `StreamRegistry`

**Files:**
- Create: `apps/api/app/events/streams.py`
- Modify: `apps/api/app/events/publisher.py` (becomes a thin shim)
- Modify: `apps/api/app/services/task_service.py` (call `publish_behavioral`)

- [ ] **Step 1: Write `apps/api/app/events/streams.py`**

```python
"""Redis Streams: publisher + stream/group registry + dedup pattern.

CONSUMER-SIDE DEDUP PATTERN (frozen here so Week 5+ consumers inherit one shape):
  SADD consumer:<group>:seen <event_id> EX 86400 NX
  If 0 → already seen, ack and skip.
  If 1 → process, then XACK.

Streams + groups are created idempotently at app startup via StreamRegistry.bootstrap().
Spec §3.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel
from redis.asyncio import Redis
from redis.exceptions import ResponseError

logger = logging.getLogger(__name__)

DEFAULT_MAXLEN = 100_000  # spec §5 bend #6


@dataclass(frozen=True)
class StreamSpec:
    name: str
    groups: tuple[str, ...]


STREAMS: tuple[StreamSpec, ...] = (
    StreamSpec("events:tasks", ("capture-svc", "analytics-svc")),
    StreamSpec("events:mood_energy", ("capture-svc", "analytics-svc")),
    StreamSpec("events:calendar", ("scheduler-svc", "analytics-svc")),
    StreamSpec("events:agent", ("agent-svc", "analytics-svc")),
)


def dlq_stream(source: str, group: str) -> str:
    return f"{source}:dlq:{group}"


EventClass = Literal["behavioral", "operational"]


class EventPublisher:
    """Typed publisher. Callers pick behavioral vs operational at the call site."""

    def __init__(self, redis: Redis, *, maxlen: int = DEFAULT_MAXLEN) -> None:
        self._redis = redis
        self._maxlen = maxlen

    async def publish_behavioral(self, stream: str, event: BaseModel) -> str:
        """Publish a behavioral event. Week 5+ consumers also insert into behavior_events."""
        return await self._xadd(stream, event, kind="behavioral")

    async def publish_operational(self, stream: str, event: BaseModel) -> str:
        """Publish an operational event. Stream-only; never enters behavior_events."""
        return await self._xadd(stream, event, kind="operational")

    async def _xadd(self, stream: str, event: BaseModel, *, kind: EventClass) -> str:
        # event_id must be on the event envelope (lockin_events base contract).
        event_id = getattr(event, "event_id", None)
        if event_id is None:
            raise ValueError(f"{type(event).__name__} missing event_id; cannot publish")
        msg_id = await self._redis.xadd(
            stream,
            {
                "event_id": str(event_id),
                "kind": kind,
                "data": event.model_dump_json(),
            },
            maxlen=self._maxlen,
            approximate=True,
        )
        return str(msg_id)


class StreamRegistry:
    """Idempotent bootstrap of streams + consumer groups (spec §3)."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def bootstrap(self) -> None:
        for spec in STREAMS:
            for group in spec.groups:
                try:
                    await self._redis.xgroup_create(
                        spec.name, group, id="$", mkstream=True
                    )
                    logger.info("created consumer group", stream=spec.name, group=group)
                except ResponseError as e:
                    if "BUSYGROUP" not in str(e):
                        raise
```

- [ ] **Step 2: Make `publisher.py` a back-compat shim**

Replace the old contents:
```python
"""Backwards-compat re-export. Prefer importing from app.events.streams."""

from app.events.streams import EventPublisher, StreamRegistry

__all__ = ["EventPublisher", "StreamRegistry"]


def get_redis():
    from app.core.config import settings
    from redis.asyncio import Redis

    return Redis.from_url(settings.REDIS_URL, decode_responses=True)
```

- [ ] **Step 3: Update `TaskService` to call `publish_behavioral`**

In `apps/api/app/services/task_service.py`, find the call to `publisher.publish(...)` and change to `publisher.publish_behavioral(...)`. Run `cd apps/api && uv run pytest tests/ -q -k task` — expect green.

- [ ] **Step 4: Wire `StreamRegistry.bootstrap()` into the FastAPI lifespan**

In `apps/api/app/main.py`'s `lifespan` function, add (inside the `try`, before `yield`):
```python
from app.events.streams import StreamRegistry
from app.events.publisher import get_redis

registry_redis = get_redis()
try:
    await StreamRegistry(registry_redis).bootstrap()
    logger.info("event streams bootstrapped")
finally:
    await registry_redis.aclose()
```

- [ ] **Step 5: Smoke-test bootstrap against real Redis**

```bash
cd apps/api
uv run uvicorn app.main:app --port 8001 &
sleep 3
docker exec lockin-redis redis-cli XINFO GROUPS events:tasks
kill %1
```
Expected: two groups, `capture-svc` and `analytics-svc`.

- [ ] **Step 6: Commit**

```bash
git add apps/api/app/events/streams.py apps/api/app/events/publisher.py apps/api/app/services/task_service.py apps/api/app/main.py
git commit -m "refactor(events): typed publisher (behavioral/operational), MAXLEN cap, StreamRegistry"
```

## Task 22: XTRIM Slice 0 entries that predate `event_id`

**Files:**
- Create: `apps/api/scripts/trim_pre_event_id_entries.py`

Slice 0 emitted to `events:tasks` without the `event_id` field on the stream entry. Week 5+ consumers will choke on those entries during backlog drain. Trim them now.

- [ ] **Step 1: Write the script**

```python
"""One-shot: trim pre-event_id entries from events:tasks.

Defensible because Slice 0 was local-dev-only with no consumers running yet.
Executed as part of §3 deploy. Spec §3 bend #4.
"""

from __future__ import annotations

import asyncio
import time

from app.events.publisher import get_redis


async def main() -> None:
    cutoff_ms = int(time.time() * 1000)
    redis = get_redis()
    try:
        trimmed = await redis.xtrim("events:tasks", minid=cutoff_ms - 60_000)
        print(f"Trimmed {trimmed} entries from events:tasks (cutoff {cutoff_ms - 60_000})")
    finally:
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Run it**

```bash
cd apps/api
uv run python scripts/trim_pre_event_id_entries.py
docker exec lockin-redis redis-cli XLEN events:tasks
```
Expected: low or zero (no Slice 0 entries in local dev anyway, but the script will run cleanly on first execution of any environment).

- [ ] **Step 3: Commit**

```bash
git add apps/api/scripts/trim_pre_event_id_entries.py
git commit -m "chore(events): one-shot script to trim Slice 0 pre-event_id stream entries"
```

## Task 23: `Reaper` — XCLAIM JUSTID IDLE 0 unstickier

**Files:**
- Create: `apps/api/app/jobs/__init__.py`
- Create: `apps/api/app/jobs/reaper.py`
- Create: `apps/api/tests/test_event_spine.py` (initial scaffold)

- [ ] **Step 1: Write the reaper module**

```python
"""Reaper: marks stuck stream entries eligible for retry.

NOT an owner — does not claim entries into its own consumer name.
Uses XCLAIM ... JUSTID IDLE 0 to reset the idle clock so the original
consumer picks them up on its next read.

DLQ routing is owned by the consumer (DLQRouter), not the reaper.

Spec §3 bend #1.
"""

from __future__ import annotations

import logging

from redis.asyncio import Redis

from app.events.streams import STREAMS

logger = logging.getLogger(__name__)

IDLE_THRESHOLD_MS = 5 * 60 * 1000


class Reaper:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def sweep_once(self) -> int:
        """Sweep every (stream, group). Returns total entries unstuck."""
        total = 0
        for spec in STREAMS:
            for group in spec.groups:
                total += await self._sweep_one(spec.name, group)
        return total

    async def _sweep_one(self, stream: str, group: str) -> int:
        pending = await self._redis.xpending_range(
            stream, group, min="-", max="+", count=100, idle=IDLE_THRESHOLD_MS
        )
        if not pending:
            return 0
        # Group entries by original consumer so we can reset their idle without
        # transferring ownership.
        by_consumer: dict[str, list[str]] = {}
        for entry in pending:
            by_consumer.setdefault(entry["consumer"], []).append(entry["message_id"])
        for consumer, ids in by_consumer.items():
            await self._redis.xclaim(
                stream,
                group,
                consumer,
                min_idle_time=0,
                message_ids=ids,
                idle=0,
                justid=True,
            )
        logger.info(
            "reaper unstuck", stream=stream, group=group, count=len(pending)
        )
        return len(pending)
```

- [ ] **Step 2: Write the unit test (mocks XPENDING/XCLAIM)**

```python
"""Event spine tests (spec §3)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.jobs.reaper import IDLE_THRESHOLD_MS, Reaper


@pytest.mark.asyncio
async def test_reaper_resets_idle_without_taking_ownership() -> None:
    redis = AsyncMock()
    redis.xpending_range.return_value = [
        {"message_id": "1-0", "consumer": "capture-svc-1", "time_since_delivered": 600_000, "times_delivered": 1},
        {"message_id": "1-1", "consumer": "capture-svc-2", "time_since_delivered": 600_000, "times_delivered": 1},
        {"message_id": "2-0", "consumer": "capture-svc-1", "time_since_delivered": 600_000, "times_delivered": 1},
    ]
    reaper = Reaper(redis)
    n = await reaper._sweep_one("events:tasks", "capture-svc")
    assert n == 3
    # Two XCLAIM calls, grouped by original consumer; neither transfers to "reaper".
    consumers_used = {call.args[2] for call in redis.xclaim.call_args_list}
    assert consumers_used == {"capture-svc-1", "capture-svc-2"}
    for call in redis.xclaim.call_args_list:
        assert call.kwargs.get("justid") is True
        assert call.kwargs.get("idle") == 0
```

- [ ] **Step 3: Run**

```bash
cd apps/api
uv run pytest tests/test_event_spine.py::test_reaper_resets_idle_without_taking_ownership -v
```
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/api/app/jobs/__init__.py apps/api/app/jobs/reaper.py apps/api/tests/test_event_spine.py
git commit -m "feat(events): Reaper resets stuck-entry idle without taking ownership"
```

## Task 24: `DLQRouter` — per-(stream, group) DLQ with rich error context

**Files:**
- Create: `apps/api/app/events/dlq.py`
- Modify: `apps/api/tests/test_event_spine.py` (append test)

- [ ] **Step 1: Write the module**

```python
"""DLQ routing: when a consumer hits >3 retries, push to per-(stream, group) DLQ.

DLQ entry shape (spec §3 bend #2):
  original_id, consumer_group, error_class, failure_reason,
  first_failure_at, last_failure_at, failure_count

Streams: events:<source>:dlq:<group>. Eight DLQ streams total
(4 main x 2 groups each).
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

from redis.asyncio import Redis

from app.events.streams import dlq_stream

MAX_DELIVERIES = 3


class DLQRouter:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def should_route(self, delivery_count: int) -> bool:
        return delivery_count > MAX_DELIVERIES

    async def route(
        self,
        *,
        source_stream: str,
        consumer_group: str,
        original_id: str,
        original_payload: dict[str, str],
        exc: BaseException,
        first_failure_at: datetime,
        failure_count: int,
    ) -> str:
        now = datetime.now(timezone.utc)
        entry = {
            "original_id": original_id,
            "consumer_group": consumer_group,
            "error_class": type(exc).__name__,
            "failure_reason": str(exc)[:1024],
            "first_failure_at": first_failure_at.isoformat(),
            "last_failure_at": now.isoformat(),
            "failure_count": str(failure_count),
            "original_payload": json.dumps(original_payload),
        }
        return str(
            await self._redis.xadd(dlq_stream(source_stream, consumer_group), entry)
        )
```

- [ ] **Step 2: Append the DLQ test**

```python
from datetime import datetime, timezone

from app.events.dlq import DLQRouter


@pytest.mark.asyncio
async def test_dlq_router_records_full_context() -> None:
    redis = AsyncMock()
    redis.xadd.return_value = "dlq-1-0"
    router = DLQRouter(redis)
    msg_id = await router.route(
        source_stream="events:tasks",
        consumer_group="capture-svc",
        original_id="1-0",
        original_payload={"event_id": "01abc", "data": "{}"},
        exc=ValueError("schema mismatch"),
        first_failure_at=datetime(2026, 5, 22, 10, 0, tzinfo=timezone.utc),
        failure_count=4,
    )
    assert msg_id == "dlq-1-0"
    redis.xadd.assert_awaited_once()
    args, _ = redis.xadd.call_args
    assert args[0] == "events:tasks:dlq:capture-svc"
    entry = args[1]
    assert entry["error_class"] == "ValueError"
    assert entry["failure_reason"] == "schema mismatch"
    assert entry["failure_count"] == "4"
```

- [ ] **Step 3: Run**

```bash
cd apps/api
uv run pytest tests/test_event_spine.py -v
```
Expected: 2 PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/api/app/events/dlq.py apps/api/tests/test_event_spine.py
git commit -m "feat(events): DLQRouter routes failed entries to per-(stream, group) DLQ"
```

## Task 25: Real-Redis integration test — consumer group resumption

**Files:**
- Modify: `apps/api/tests/test_event_spine.py`

This test cannot use fakeredis — `XINFO GROUPS` semantics diverge. Uses the running docker-compose redis.

- [ ] **Step 1: Append test**

```python
import os

from redis.asyncio import Redis as RealRedis

from app.events.streams import EventPublisher, StreamRegistry, STREAMS


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/15")  # /15 = test db


@pytest.fixture
async def real_redis():
    redis = RealRedis.from_url(REDIS_URL, decode_responses=True)
    await redis.flushdb()
    yield redis
    await redis.flushdb()
    await redis.aclose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_consumer_group_resumption_no_dupes_no_drops(real_redis) -> None:
    """Produce 10k entries, ack 5k, restart consumer, verify resume at 5001."""
    await StreamRegistry(real_redis).bootstrap()
    # Manual XADD (bypass typed publisher to keep test focused on stream semantics).
    for i in range(10_000):
        await real_redis.xadd("events:tasks", {"event_id": f"id-{i}", "data": "{}"}, maxlen=20_000)

    # First consumer instance: ack first 5k.
    acked: list[str] = []
    while len(acked) < 5_000:
        resp = await real_redis.xreadgroup(
            "capture-svc", "consumer-A", {"events:tasks": ">"}, count=1000
        )
        for _stream, entries in resp:
            for entry_id, _data in entries:
                await real_redis.xack("events:tasks", "capture-svc", entry_id)
                acked.append(entry_id)

    # Simulate crash + restart with the same consumer name.
    acked2: list[str] = []
    while len(acked2) < 5_000:
        resp = await real_redis.xreadgroup(
            "capture-svc", "consumer-A", {"events:tasks": ">"}, count=1000
        )
        if not resp:
            break
        for _stream, entries in resp:
            for entry_id, _data in entries:
                await real_redis.xack("events:tasks", "capture-svc", entry_id)
                acked2.append(entry_id)

    info = await real_redis.xinfo_groups("events:tasks")
    capture = next(g for g in info if g["name"] == "capture-svc")
    assert capture["pending"] == 0
    assert len(acked) + len(acked2) == 10_000
    assert len(set(acked) & set(acked2)) == 0  # no dupes
```

- [ ] **Step 2: Run**

```bash
cd apps/api
uv run pytest tests/test_event_spine.py::test_consumer_group_resumption_no_dupes_no_drops -v -m integration
```
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add apps/api/tests/test_event_spine.py
git commit -m "test(events): real-Redis integration test for consumer-group resumption"
```

## Task 26: Slow integration test — reaper against real clock

**Files:**
- Modify: `apps/api/tests/test_event_spine.py`

- [ ] **Step 1: Append `@pytest.mark.slow` test**

```python
import asyncio


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_reaper_unsticks_real_redis_entries(real_redis) -> None:
    """Read entries, leave them unacked, sleep past idle threshold, run reaper, verify retry-eligible."""
    await StreamRegistry(real_redis).bootstrap()
    for i in range(3):
        await real_redis.xadd("events:tasks", {"event_id": f"id-{i}", "data": "{}"})
    # Read without acking.
    await real_redis.xreadgroup(
        "capture-svc", "consumer-X", {"events:tasks": ">"}, count=3
    )
    # Sleep 6 minutes (past 5-min idle threshold). Real wall clock; cannot be mocked.
    await asyncio.sleep(310)

    from app.jobs.reaper import Reaper
    n = await Reaper(real_redis).sweep_once()
    assert n >= 3

    # After reaper resets idle to 0, a new XREADGROUP with the same consumer
    # should re-deliver via the PEL.
    pending_before = await real_redis.xpending("events:tasks", "capture-svc")
    assert pending_before["pending"] == 3
```

- [ ] **Step 2: Configure pytest markers in `apps/api/pyproject.toml`**

```toml
markers = [
    "integration: requires docker compose services",
    "slow: long-running integration test (>1min); run in CI not on every local push",
]
```

- [ ] **Step 3: Verify the slow test is excluded from default runs but included with `-m slow`**

```bash
cd apps/api
uv run pytest -q -m "not slow"  # default runs
uv run pytest -q -m slow tests/test_event_spine.py  # slow only
```
Default: passes everything except the 310s test. Slow run: passes after ~5 minutes.

- [ ] **Step 4: Commit**

```bash
git add apps/api/tests/test_event_spine.py apps/api/pyproject.toml
git commit -m "test(events): slow integration test — reaper against real wall clock"
```

---

# Phase F — Frontend scaffolding split (Day 6 morning, 3hr max, conditional)

**Conditional:** Execute only if Day 4-5 review showed slice on-pace. If running behind, skip Phase F here and roll its tasks into Phase L (Day 10). This split is the buffer per spec §7 bend #2.

## Task 27: `sanitize_next_param` helper + tests

**Files:**
- Create: `apps/web/src/lib/auth/redirect.ts`
- Create: `apps/web/src/lib/auth/redirect.test.ts`

- [ ] **Step 1: Write failing tests first**

```typescript
import { describe, expect, it } from "vitest";
import { sanitizeNextParam } from "./redirect";

describe("sanitizeNextParam", () => {
  const SAFE = "/today";

  it.each([
    ["//evil.com", SAFE],
    ["https://evil.com", SAFE],
    ["/api/auth/csrf", SAFE],
    ["%2F%2Fevil.com", SAFE],
    ["%252F%252Fevil.com", SAFE],
    ["/\\evil.com", SAFE],
    ["%5Cevil.com", SAFE],
    ["/today", "/today"],
    ["/schedule?day=2026-05-22", "/schedule?day=2026-05-22"],
    ["/settings/integrations", "/settings/integrations"],
    [null, SAFE],
    ["", SAFE],
  ])("input %p → %p", (input, expected) => {
    expect(sanitizeNextParam(input)).toBe(expected);
  });
});
```

Run: `cd apps/web && pnpm vitest run src/lib/auth/redirect.test.ts` → FAIL (module not found).

- [ ] **Step 2: Implement the helper**

```typescript
const SAFE_DEFAULT = "/today";

export function sanitizeNextParam(raw: string | null): string {
  if (raw === null || raw === "") return SAFE_DEFAULT;
  // Rule 0: backslash poison (spec §6 patch).
  if (raw.includes("\\")) return SAFE_DEFAULT;
  if (!passesShape(raw)) return SAFE_DEFAULT;
  // Defeat double-encoding bypasses by re-checking the decoded form.
  let decoded = raw;
  try {
    decoded = decodeURIComponent(raw);
  } catch {
    return SAFE_DEFAULT;
  }
  if (decoded.includes("\\")) return SAFE_DEFAULT;
  if (!passesShape(decoded)) return SAFE_DEFAULT;
  return raw;
}

function passesShape(value: string): boolean {
  return value.startsWith("/") && !value.startsWith("//") && !value.startsWith("/api/");
}
```

- [ ] **Step 3: Re-run tests → all PASS**

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/lib/auth/redirect.ts apps/web/src/lib/auth/redirect.test.ts
git commit -m "feat(web): sanitize_next_param defends against open-redirect (incl. backslash)"
```

## Task 28: `EmptyState`, `Banner`, `Skeleton` components in `@lockin/ui`

**Files:**
- Create: `packages/ui/src/components/empty-state/{index,stories,test}.tsx`
- Create: `packages/ui/src/components/banner/{index,stories,test}.tsx`
- Create: `packages/ui/src/components/skeleton/{index,stories,test}.tsx`
- Modify: `packages/ui/src/index.ts`

- [ ] **Step 1: `EmptyState`**

`packages/ui/src/components/empty-state/index.tsx`:
```tsx
import type { ReactNode } from "react";
import { Button } from "../button";
import { Stack } from "../stack";
import { Text } from "../text";

export interface EmptyStateProps {
  title: string;
  body?: string;
  action?: { label: string; onClick: () => void };
  icon?: ReactNode;
}

export function EmptyState({ title, body, action, icon }: EmptyStateProps) {
  return (
    <Stack gap={4} align="center" className="py-16 text-center">
      {icon ? <div aria-hidden>{icon}</div> : null}
      <Text as="h2" size="lg" weight="semibold">{title}</Text>
      {body ? <Text muted>{body}</Text> : null}
      {action ? (
        <Button onClick={action.onClick}>{action.label}</Button>
      ) : null}
    </Stack>
  );
}
```

- [ ] **Step 2: `Banner`**

`packages/ui/src/components/banner/index.tsx`:
```tsx
import type { ReactNode } from "react";
import { useState } from "react";

export interface BannerProps {
  children: ReactNode;
  dismissible?: boolean;
  tone?: "info" | "warning";
}

export function Banner({ children, dismissible = true, tone = "info" }: BannerProps) {
  const [open, setOpen] = useState(true);
  if (!open) return null;
  const toneClass = tone === "warning" ? "bg-amber-50 text-amber-900" : "bg-blue-50 text-blue-900";
  return (
    <div role="status" className={`flex items-center justify-between px-4 py-2 ${toneClass}`}>
      <div>{children}</div>
      {dismissible ? (
        <button
          type="button"
          onClick={() => setOpen(false)}
          aria-label="Dismiss"
          className="ml-4 text-sm underline focus-visible:outline-2 focus-visible:outline-offset-2"
        >
          Dismiss
        </button>
      ) : null}
    </div>
  );
}
```

- [ ] **Step 3: `Skeleton`**

`packages/ui/src/components/skeleton/index.tsx`:
```tsx
export interface SkeletonProps {
  width?: string;
  height?: string;
  rounded?: "sm" | "md" | "full";
}

export function Skeleton({ width = "100%", height = "1rem", rounded = "md" }: SkeletonProps) {
  const radius = rounded === "full" ? "rounded-full" : rounded === "sm" ? "rounded-sm" : "rounded-md";
  return (
    <div
      aria-hidden
      className={`animate-pulse bg-neutral-200 ${radius}`}
      style={{ width, height }}
    />
  );
}
```

- [ ] **Step 4: Storybook stories and tests for each**

Each component gets a `stories.tsx` exporting at minimum one `Default` story and a `test.tsx` rendering once with `render(...)` and asserting basic presence. Pattern (illustrated for EmptyState):

`empty-state/stories.tsx`:
```tsx
import type { Meta, StoryObj } from "@storybook/react";
import { EmptyState } from "./index";

const meta: Meta<typeof EmptyState> = { component: EmptyState, title: "EmptyState" };
export default meta;
export const Default: StoryObj<typeof EmptyState> = {
  args: { title: "Capture your first task", body: "Press ⌘K to open the palette." },
};
```

`empty-state/test.tsx`:
```tsx
import { render, screen } from "@testing-library/react";
import { EmptyState } from "./index";

test("renders title", () => {
  render(<EmptyState title="hello" />);
  expect(screen.getByText("hello")).toBeInTheDocument();
});
```

- [ ] **Step 5: Re-export from `packages/ui/src/index.ts`**

```typescript
export { EmptyState } from "./components/empty-state";
export type { EmptyStateProps } from "./components/empty-state";
export { Banner } from "./components/banner";
export type { BannerProps } from "./components/banner";
export { Skeleton } from "./components/skeleton";
export type { SkeletonProps } from "./components/skeleton";
```

- [ ] **Step 6: Run tests + Storybook build**

```bash
pnpm --filter @lockin/ui test
pnpm --filter @lockin/ui build-storybook
```

- [ ] **Step 7: Commit**

```bash
git add packages/ui/src/components/empty-state packages/ui/src/components/banner packages/ui/src/components/skeleton packages/ui/src/index.ts
git commit -m "feat(ui): EmptyState, Banner, Skeleton primitives + stories"
```

## Task 29: `FloatingActionButton` + `Sidebar` + `BottomTabNav` shells

**Files:**
- Create: `packages/ui/src/components/floating-action-button/{index,stories,test}.tsx`
- Create: `packages/ui/src/components/sidebar/{index,stories,test}.tsx`
- Create: `packages/ui/src/components/bottom-tab-nav/{index,stories,test}.tsx`
- Modify: `packages/ui/src/index.ts`

- [ ] **Step 1: FloatingActionButton**

`floating-action-button/index.tsx`:
```tsx
import type { ReactNode } from "react";

export interface FloatingActionButtonProps {
  onClick: () => void;
  "aria-label": string;
  children: ReactNode;
}

export function FloatingActionButton({ onClick, "aria-label": ariaLabel, children }: FloatingActionButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={ariaLabel}
      className="fixed bottom-20 right-4 z-30 inline-flex h-14 w-14 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg focus-visible:outline-2 focus-visible:outline-offset-2 md:hidden"
    >
      {children}
    </button>
  );
}
```

- [ ] **Step 2: Sidebar** (md+, collapsible). Props: `items: Array<{href, label, icon}>`, `currentPath`. Renders `<aside>` with `<nav>`, semantic HTML. Hidden on `<md` via `hidden md:flex`.

```tsx
import Link from "next/link";
import type { ReactNode } from "react";

export interface SidebarItem {
  href: string;
  label: string;
  icon?: ReactNode;
}

export interface SidebarProps {
  items: SidebarItem[];
  currentPath: string;
  header?: ReactNode;
}

export function Sidebar({ items, currentPath, header }: SidebarProps) {
  return (
    <aside className="hidden md:flex md:w-60 md:flex-col md:border-r md:border-neutral-200">
      {header ? <div className="p-4">{header}</div> : null}
      <nav aria-label="Primary" className="flex flex-col gap-1 p-2">
        {items.map((item) => {
          const active = currentPath === item.href || currentPath.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2 rounded px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 ${active ? "bg-neutral-100 font-semibold" : "hover:bg-neutral-50"}`}
              aria-current={active ? "page" : undefined}
            >
              {item.icon}<span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
```

- [ ] **Step 3: BottomTabNav** (mobile only). Three slots: Today, Schedule, Settings.

```tsx
import Link from "next/link";
import type { ReactNode } from "react";

export interface BottomTabItem {
  href: string;
  label: string;
  icon: ReactNode;
}

export interface BottomTabNavProps {
  items: BottomTabItem[];  // expects exactly 3
  currentPath: string;
}

export function BottomTabNav({ items, currentPath }: BottomTabNavProps) {
  return (
    <nav
      aria-label="Primary mobile"
      className="fixed inset-x-0 bottom-0 z-20 flex border-t border-neutral-200 bg-white md:hidden"
    >
      {items.map((item) => {
        const active = currentPath === item.href || currentPath.startsWith(item.href + "/");
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex flex-1 flex-col items-center gap-1 py-2 text-xs focus-visible:outline-2 focus-visible:outline-offset-2 ${active ? "font-semibold text-blue-700" : "text-neutral-600"}`}
            aria-current={active ? "page" : undefined}
          >
            {item.icon}{item.label}
          </Link>
        );
      })}
    </nav>
  );
}
```

- [ ] **Step 4: Stories + tests + re-export** (pattern from Task 28).

- [ ] **Step 5: Commit**

```bash
git add packages/ui/src/components/floating-action-button packages/ui/src/components/sidebar packages/ui/src/components/bottom-tab-nav packages/ui/src/index.ts
git commit -m "feat(ui): FAB + Sidebar + BottomTabNav shells (3-tab nav per §6 bend #4)"
```

## Task 30: Route group skeletons (empty `(authed)/` pages)

**Files:**
- Create: `apps/web/src/app/(authed)/layout.tsx`
- Create: `apps/web/src/app/(authed)/today/page.tsx`
- Create: `apps/web/src/app/(authed)/schedule/page.tsx`
- Create: `apps/web/src/app/(authed)/settings/layout.tsx`
- Create: `apps/web/src/app/(authed)/settings/page.tsx`
- Create: `apps/web/src/app/(authed)/settings/integrations/page.tsx`

This task creates placeholder pages so Phase L (Day 10) only does wiring, not scaffolding. Theme/FAB/banner integration lands in Phase L.

- [ ] **Step 1: `(authed)/layout.tsx`**

```tsx
import type { ReactNode } from "react";
import { Sidebar, BottomTabNav } from "@lockin/ui";

const navItems = [
  { href: "/today", label: "Today" },
  { href: "/schedule", label: "Schedule" },
  { href: "/settings", label: "Settings" },
];

export default function AuthedLayout({ children }: { children: ReactNode }) {
  // currentPath wiring lands in Phase L via usePathname() to keep this server-rendered today.
  return (
    <div className="flex min-h-screen">
      <Sidebar items={navItems} currentPath="" />
      <main className="flex-1 pb-16 md:pb-0">
        <a href="#main-content" className="sr-only focus:not-sr-only">Skip to content</a>
        <div id="main-content">{children}</div>
      </main>
      <BottomTabNav items={navItems.map((i) => ({ ...i, icon: null }))} currentPath="" />
    </div>
  );
}
```

- [ ] **Step 2: `today/page.tsx` (empty state placeholder; palette wiring lands in Phase L)**

```tsx
"use client";
import { EmptyState } from "@lockin/ui";

export default function TodayPage() {
  return (
    <EmptyState
      title="Capture your first task"
      body="Press ⌘K to open the palette."
      action={{ label: "Open palette (⌘K)", onClick: () => { /* wired in Phase L */ } }}
    />
  );
}
```

- [ ] **Step 3: `schedule/page.tsx`**

```tsx
import { EmptyState } from "@lockin/ui";

export default function SchedulePage() {
  return (
    <EmptyState
      title="Connect your calendar"
      body="LockIn schedules around real meetings."
      action={{ label: "Go to integrations", onClick: () => { window.location.href = "/settings/integrations"; } }}
    />
  );
}
```
(Mark as `"use client"` since the action uses `window`.)

- [ ] **Step 4: `settings/layout.tsx`, `settings/page.tsx`, `settings/integrations/page.tsx`** — minimal pages with section headings + placeholder text. Integrations page renders "Connect calendar" button stub; real wiring in Phase K.

- [ ] **Step 5: Sanity-check the build**

```bash
pnpm --filter @lockin/web build
```
Expected: build succeeds.

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/app/\(authed\)
git commit -m "feat(web): route group skeleton — (authed)/today, /schedule, /settings"
```

---

# Phase G — API gateway middleware stack (Days 6-7)

Middleware register order in `apps/api/app/main.py`: ErrorEnvelope OUTERMOST (added FIRST via `add_middleware`), then Idempotency, JWT, RateLimit, CORS, RequestID. Starlette wraps each new `add_middleware` around the existing stack, so first-added is outermost.

Inbound flow: `ErrorEnvelope → RequestID → CORS → RateLimit → JWT → Idempotency → route`.

## Task 31: `RequestID` middleware

**Files:**
- Create: `apps/api/app/middleware/__init__.py`
- Create: `apps/api/app/middleware/request_id.py`
- Create: `apps/api/tests/middleware/__init__.py`
- Create: `apps/api/tests/middleware/test_request_id.py`

- [ ] **Step 1: Implement**

```python
"""Request-ID middleware: generates uuid7 if absent, propagates to logs + response header."""

from __future__ import annotations

from contextvars import ContextVar

import uuid_utils
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
HEADER = "X-Request-Id"


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get(HEADER) or str(uuid_utils.uuid7())
        token = request_id_ctx.set(rid)
        try:
            response: Response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        response.headers[HEADER] = rid
        return response
```

- [ ] **Step 2: Test**

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.request_id import RequestIDMiddleware, HEADER, request_id_ctx


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/x")
    def x():
        return {"rid": request_id_ctx.get()}

    return app


def test_generates_request_id_when_absent():
    client = TestClient(_build_app())
    r = client.get("/x")
    assert r.status_code == 200
    assert HEADER in r.headers
    assert len(r.headers[HEADER]) == 36  # UUID
    assert r.json()["rid"] == r.headers[HEADER]


def test_preserves_inbound_request_id():
    client = TestClient(_build_app())
    r = client.get("/x", headers={HEADER: "supplied-by-caller"})
    assert r.headers[HEADER] == "supplied-by-caller"
    assert r.json()["rid"] == "supplied-by-caller"
```

- [ ] **Step 3: Run + commit**

```bash
cd apps/api
uv run pytest tests/middleware/test_request_id.py -v
git add apps/api/app/middleware/__init__.py apps/api/app/middleware/request_id.py apps/api/tests/middleware/
git commit -m "feat(api): RequestID middleware (uuid7 propagation via contextvar)"
```

## Task 32: `ErrorEnvelope` middleware (must be outermost)

**Files:**
- Create: `apps/api/app/middleware/error_envelope.py`
- Create: `apps/api/tests/middleware/test_error_envelope.py`

- [ ] **Step 1: Implement**

```python
"""Error envelope middleware — OUTERMOST so it catches any exception in the middleware
stack itself, not just route handlers. Spec §4 bend #1."""

from __future__ import annotations

import os

import sentry_sdk
from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.middleware.request_id import request_id_ctx


class ErrorEnvelopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException as exc:
            return self._envelope(exc.status_code, code=str(exc.status_code), message=exc.detail)
        except Exception as exc:  # noqa: BLE001 — outermost catch
            sentry_sdk.capture_exception(exc)
            if os.getenv("ENV", "local") == "local":
                # Local dev: surface the message for debugging.
                return self._envelope(500, code="internal_error", message=repr(exc))
            return self._envelope(500, code="internal_error", message="Internal Server Error")

    def _envelope(self, status: int, *, code: str, message: str) -> Response:
        return JSONResponse(
            status_code=status,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "request_id": request_id_ctx.get(),
                }
            },
        )
```

- [ ] **Step 2: Test that envelope catches exceptions from OTHER middlewares**

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.error_envelope import ErrorEnvelopeMiddleware
from app.middleware.request_id import RequestIDMiddleware


class _BoomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        raise RuntimeError("middleware-level failure")


def _app_with_boom_after_envelope():
    app = FastAPI()
    # Add in reverse of inbound order: innermost first.
    app.add_middleware(_BoomMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(ErrorEnvelopeMiddleware)  # outermost, added last

    @app.get("/x")
    def x():
        return {"ok": True}

    return app


def test_envelope_catches_middleware_exception():
    client = TestClient(_app_with_boom_after_envelope(), raise_server_exceptions=False)
    r = client.get("/x")
    assert r.status_code == 500
    body = r.json()
    assert body["error"]["code"] == "internal_error"
    assert body["error"]["request_id"] is not None
```

- [ ] **Step 3: Run + commit**

```bash
cd apps/api
uv run pytest tests/middleware/test_error_envelope.py -v
git add apps/api/app/middleware/error_envelope.py apps/api/tests/middleware/test_error_envelope.py
git commit -m "feat(api): ErrorEnvelope middleware (outermost; catches stack exceptions)"
```

## Task 33: `CORS` middleware

**Files:**
- Create: `apps/api/app/middleware/cors.py`

- [ ] **Step 1: Thin wrapper around Starlette's**

```python
"""CORS middleware — thin wrapper picking origins from WEB_ORIGINS env (CSV)."""

from __future__ import annotations

import os

from starlette.middleware.cors import CORSMiddleware


def cors_config() -> dict:
    raw = os.getenv("WEB_ORIGINS", "")
    if raw.strip() == "*" or not raw:
        origins: list[str] = ["*"]
    else:
        origins = [o.strip() for o in raw.split(",") if o.strip()]
    return {
        "allow_origins": origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Authorization", "Content-Type", "Idempotency-Key", "X-Request-Id"],
        "expose_headers": ["X-Request-Id"],
    }
```

Usage in `main.py`: `app.add_middleware(CORSMiddleware, **cors_config())`.

- [ ] **Step 2: Commit (no separate test — Starlette's CORSMiddleware is well-tested)**

```bash
git add apps/api/app/middleware/cors.py
git commit -m "feat(api): CORS config picks origins from WEB_ORIGINS env"
```

## Task 34: `RateLimit` middleware + Lua script

**Files:**
- Create: `apps/api/app/middleware/rate_limit.lua`
- Create: `apps/api/app/middleware/rate_limit.py`
- Create: `apps/api/tests/middleware/test_rate_limit.py`

- [ ] **Step 1: Lua (fixed-window counter)**

```lua
-- Fixed-window counter. Spec §4 bend #3.
-- KEYS[1] = bucket key
-- ARGV[1] = window seconds
-- Returns: current count
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
```

- [ ] **Step 2: Middleware**

```python
"""Fixed-window rate limit via Redis. Fails OPEN on Redis error (spec §4 bend #3)."""

from __future__ import annotations

import logging
from pathlib import Path

import sentry_sdk
from redis.asyncio import Redis
from redis.exceptions import NoScriptError, RedisError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

USER_LIMIT = 100  # per 60s
IP_LIMIT = 1000  # per 60s
WINDOW_S = 60

_SCRIPT_PATH = Path(__file__).with_name("rate_limit.lua")


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis: Redis) -> None:
        super().__init__(app)
        self._redis = redis
        self._sha: str | None = None
        self._script = _SCRIPT_PATH.read_text()

    async def _eval(self, key: str) -> int | None:
        try:
            if self._sha is None:
                self._sha = await self._redis.script_load(self._script)
            try:
                result = await self._redis.evalsha(self._sha, 1, key, WINDOW_S)
            except NoScriptError:
                result = await self._redis.eval(self._script, 1, key, WINDOW_S)
            return int(result) if result is not None else None
        except RedisError as exc:
            logger.warning("rate limit redis error; failing open", exc_info=exc)
            sentry_sdk.add_breadcrumb(category="rate_limit", message="redis_error", level="warning")
            return None

    async def dispatch(self, request: Request, call_next):
        user_id = getattr(request.state, "user_id", None)
        ip = request.client.host if request.client else "unknown"

        if user_id is not None:
            count = await self._eval(f"rl:user:{user_id}")
            if count is not None and count > USER_LIMIT:
                return JSONResponse(
                    status_code=429,
                    content={"error": {"code": "rate_limited", "message": "user rate limit exceeded"}},
                )

        count_ip = await self._eval(f"rl:ip:{ip}")
        if count_ip is not None and count_ip > IP_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "rate_limited", "message": "ip rate limit exceeded"}},
            )

        return await call_next(request)
```

- [ ] **Step 3: Tests — fail-open on ConnectionError AND on None reply**

```python
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError

from app.middleware.rate_limit import RateLimitMiddleware


def _app(redis_mock) -> TestClient:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, redis=redis_mock)

    @app.get("/x")
    def x(): return {"ok": True}

    return TestClient(app)


def test_fail_open_on_connection_error():
    redis = AsyncMock()
    redis.script_load.side_effect = RedisConnectionError("down")
    client = _app(redis)
    r = client.get("/x")
    assert r.status_code == 200


def test_fail_open_on_none_reply():
    redis = AsyncMock()
    redis.script_load.return_value = "sha"
    redis.evalsha.return_value = None  # partial failure
    client = _app(redis)
    r = client.get("/x")
    assert r.status_code == 200


def test_blocks_over_user_limit():
    redis = AsyncMock()
    redis.script_load.return_value = "sha"
    redis.evalsha.side_effect = [101, 50]  # user over, ip under
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, redis=redis)

    @app.middleware("http")
    async def attach_user(req, call_next):
        req.state.user_id = "u-1"
        return await call_next(req)

    @app.get("/x")
    def x(): return {"ok": True}

    client = TestClient(app)
    r = client.get("/x")
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "rate_limited"
```

- [ ] **Step 4: Run + commit**

```bash
cd apps/api
uv run pytest tests/middleware/test_rate_limit.py -v
git add apps/api/app/middleware/rate_limit.py apps/api/app/middleware/rate_limit.lua apps/api/tests/middleware/test_rate_limit.py
git commit -m "feat(api): fixed-window rate limit (Lua), fail-open on RedisError + None reply"
```

## Task 35: `JWT` middleware with structured error codes

**Files:**
- Create: `apps/api/app/middleware/jwt.py`
- Create: `apps/api/tests/middleware/test_jwt.py`
- Create: `docs/decisions/2026-05-22-jwt-bearer-contract.md`

- [ ] **Step 1: Decision log**

`docs/decisions/2026-05-22-jwt-bearer-contract.md`:
```markdown
# JWT contract: Bearer-only, strict scheme parsing

**Date:** 2026-05-22
**Status:** Accepted

## Decision
The api accepts authentication exclusively via `Authorization: Bearer <HS256-jwt>`.
Strict parsing — any malformed header → 401 `auth_invalid_scheme`. The Week 3-4
handoff text described cookie reads; that is superseded — Slice 0 wired the BFF
to forward Bearer, and dual-mode would be overengineering for P1.

## Structured error codes
| code | meaning | BFF action |
|---|---|---|
| `auth_missing` | no Authorization header on a protected path | redirect to /login |
| `auth_invalid_scheme` | header present but not `Bearer ...` exactly | log + 401 |
| `auth_malformed` | bearer present, JWT does not parse | log + 401 |
| `auth_invalid_signature` | JWT parses but signature fails | logout user + alert |
| `auth_expired` | JWT signature valid but expired | refresh + retry |

## Anonymous paths
`/health`, `/v1/health`, `/v1/auth/*`, `/docs`, `/openapi.json`, `/v1/__debug__/*`
(local only).
```

- [ ] **Step 2: Implement JWT middleware**

```python
"""Strict-Bearer JWT validation with structured error codes. Spec §4 bend #4."""

from __future__ import annotations

import re

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.identity import user_uuid

ANONYMOUS_PREFIXES = (
    "/health",
    "/v1/health",
    "/v1/auth/",
    "/docs",
    "/openapi.json",
    "/v1/__debug__/",
)

_BEARER = re.compile(r"^Bearer ([A-Za-z0-9._-]+)$")


def _envelope(code: str) -> JSONResponse:
    return JSONResponse(status_code=401, content={"error": {"code": code, "message": code}})


class JWTMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path == p or path.startswith(p) for p in ANONYMOUS_PREFIXES):
            return await call_next(request)

        header = request.headers.get("Authorization")
        if header is None:
            return _envelope("auth_missing")
        match = _BEARER.fullmatch(header)
        if match is None:
            return _envelope("auth_invalid_scheme")
        token = match.group(1)
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return _envelope("auth_expired")
        except jwt.InvalidSignatureError:
            return _envelope("auth_invalid_signature")
        except jwt.PyJWTError:
            return _envelope("auth_malformed")

        sub = payload.get("sub")
        if not sub:
            return _envelope("auth_malformed")
        request.state.user_id = user_uuid(sub)
        return await call_next(request)
```

- [ ] **Step 3: Test each error code**

```python
import jwt as pyjwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.middleware.jwt import JWTMiddleware


def _app():
    app = FastAPI()
    app.add_middleware(JWTMiddleware)

    @app.get("/health")
    def health(): return {"ok": True}

    @app.get("/v1/protected")
    def p(): return {"ok": True}

    return TestClient(app)


def _token(**overrides):
    payload = {"sub": "google-12345", "exp": 9999999999}
    payload.update(overrides)
    return pyjwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def test_anonymous_path_open():
    assert _app().get("/health").status_code == 200


def test_missing_header():
    r = _app().get("/v1/protected")
    assert r.status_code == 401 and r.json()["error"]["code"] == "auth_missing"


def test_invalid_scheme():
    r = _app().get("/v1/protected", headers={"Authorization": "Token abc"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "auth_invalid_scheme"


def test_malformed_token():
    r = _app().get("/v1/protected", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "auth_malformed"


def test_invalid_signature():
    bad = pyjwt.encode({"sub": "g-1", "exp": 9999999999}, "wrong-secret", algorithm="HS256")
    r = _app().get("/v1/protected", headers={"Authorization": f"Bearer {bad}"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "auth_invalid_signature"


def test_expired():
    r = _app().get("/v1/protected", headers={"Authorization": f"Bearer {_token(exp=1)}"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "auth_expired"


def test_valid_passes_through():
    r = _app().get("/v1/protected", headers={"Authorization": f"Bearer {_token()}"})
    assert r.status_code == 200
```

- [ ] **Step 4: Run + commit**

```bash
cd apps/api
uv run pytest tests/middleware/test_jwt.py -v
git add apps/api/app/middleware/jwt.py apps/api/tests/middleware/test_jwt.py docs/decisions/2026-05-22-jwt-bearer-contract.md
git commit -m "feat(api): strict-Bearer JWT middleware with structured error codes"
```

## Task 36: `Idempotency` middleware + DB-session dependency wiring

**Files:**
- Create: `apps/api/app/middleware/idempotency.py`
- Modify: `apps/api/app/api/v1/deps.py` (add `get_session_into_request_state`)
- Create: `apps/api/tests/middleware/test_idempotency.py`

- [ ] **Step 1: DB-session sharing dependency**

In `apps/api/app/api/v1/deps.py` add:
```python
from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory


async def get_session_into_request_state(request: Request) -> AsyncSession:
    """Yields a session and attaches it to request.state.db so the idempotency
    middleware can join the route's transaction. Apply this as a global override
    in main.py:
        app.dependency_overrides[get_session] = get_session_into_request_state
    """
    async with async_session_factory() as session:
        request.state.db = session
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            request.state.db = None
```

- [ ] **Step 2: Implement idempotency middleware**

```python
"""Idempotency middleware: replay-cached responses for mutations.

- Mutations only (POST/PUT/PATCH/DELETE).
- Cache only 2xx and 4xx; 5xx never persisted (spec §4 bend #2).
- Request hash uses canonical body (parsed JSON re-serialized with sorted keys).
- Joins the route's DB transaction via request.state.db (spec self-review fix #4).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.db.models.idempotency_key import IdempotencyKey

MUTATIONS = {"POST", "PUT", "PATCH", "DELETE"}


async def _canonical_body(request: Request) -> bytes:
    raw = await request.body()
    if not raw:
        return b""
    ctype = request.headers.get("content-type", "")
    if "application/json" in ctype:
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return raw
        return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return raw


def _hash(method: str, path: str, query: str, body: bytes) -> bytes:
    sorted_query = "&".join(sorted(query.split("&"))) if query else ""
    h = hashlib.sha256()
    h.update(method.upper().encode())
    h.update(b"\n")
    h.update(path.encode())
    h.update(b"\n")
    h.update(sorted_query.encode())
    h.update(b"\n")
    h.update(body)
    return h.digest()


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in MUTATIONS:
            return await call_next(request)
        key = request.headers.get("Idempotency-Key")
        if not key:
            return await call_next(request)
        user_id = getattr(request.state, "user_id", None)
        if user_id is None:
            return await call_next(request)
        body = await _canonical_body(request)
        # Cache the body so the downstream route can re-read it.
        async def _receive():
            return {"type": "http.request", "body": body, "more_body": False}
        request._receive = _receive  # type: ignore[attr-defined]
        req_hash = _hash(request.method, request.url.path, request.url.query, body)

        session: AsyncSession | None = getattr(request.state, "db", None)
        if session is None:
            return await call_next(request)

        existing = (
            await session.execute(
                select(IdempotencyKey).where(
                    IdempotencyKey.user_id == user_id,
                    IdempotencyKey.client_idempotency_key == key,
                )
            )
        ).scalar_one_or_none()

        if existing is not None:
            if existing.request_hash != req_hash:
                return JSONResponse(
                    status_code=422,
                    content={"error": {"code": "idempotency_key_reused", "message": "same key, different payload"}},
                )
            return JSONResponse(status_code=existing.status_code, content=existing.response_json)

        response: Response = await call_next(request)

        if response.status_code >= 500:
            return response  # never cache 5xx

        # Buffer body for both caching and response.
        body_chunks: list[bytes] = []
        async for chunk in response.body_iterator:  # type: ignore[attr-defined]
            body_chunks.append(chunk)
        payload = b"".join(body_chunks)
        try:
            response_json: Any = json.loads(payload.decode() or "null")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return Response(content=payload, status_code=response.status_code, headers=dict(response.headers))

        session.add(
            IdempotencyKey(
                user_id=user_id,
                client_idempotency_key=key,
                request_hash=req_hash,
                response_json=response_json,
                status_code=response.status_code,
            )
        )
        # Session commit happens in get_session_into_request_state on yield exit.

        return JSONResponse(
            status_code=response.status_code,
            content=response_json,
            headers={k: v for k, v in response.headers.items() if k.lower() != "content-length"},
        )
```

- [ ] **Step 3: Test (replay correctness + 5xx skip + body-shape mismatch → 422)**

```python
import json
import uuid
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.idempotency import IdempotencyMiddleware


@pytest.mark.asyncio
async def test_replay_correctness(test_session: AsyncSession):
    """Same key + body → identical response, single DB row."""
    app = FastAPI()
    counter = {"n": 0}

    @app.middleware("http")
    async def attach(request, call_next):
        request.state.user_id = uuid.UUID(int=1)
        request.state.db = test_session
        return await call_next(request)

    app.add_middleware(IdempotencyMiddleware)

    @app.post("/x")
    async def x(body: dict):
        counter["n"] += 1
        return {"n": counter["n"], "echo": body}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as client:
        r1 = await client.post("/x", headers={"Idempotency-Key": "k1"}, json={"a": 1})
        r2 = await client.post("/x", headers={"Idempotency-Key": "k1"}, json={"a": 1})
    assert r1.json() == r2.json()
    assert counter["n"] == 1


@pytest.mark.asyncio
async def test_different_body_with_same_key_returns_422(test_session: AsyncSession):
    # ... (same setup as above)
    # First request: 200; second with different body: 422 idempotency_key_reused
    ...


@pytest.mark.asyncio
async def test_5xx_not_cached(test_session: AsyncSession):
    """Route raises 500 → no row written → retry re-executes."""
    # Assert SELECT COUNT(*) FROM idempotency_keys WHERE client_idempotency_key='k' == 0
    ...
```

(Stub the second and third tests fully when implementing — see the first as the template.)

- [ ] **Step 4: Run + commit**

```bash
cd apps/api
uv run pytest tests/middleware/test_idempotency.py -v
git add apps/api/app/middleware/idempotency.py apps/api/app/api/v1/deps.py apps/api/tests/middleware/test_idempotency.py
git commit -m "feat(api): Idempotency middleware (2xx/4xx-only, joins route txn via request.state.db)"
```

## Task 37: Register middleware stack in `main.py`

**Files:**
- Modify: `apps/api/app/main.py`

- [ ] **Step 1: Register middlewares in REVERSE inbound order**

Below the `lifespan` setup, before `fast_app.include_router`:
```python
from app.middleware.cors import cors_config
from app.middleware.error_envelope import ErrorEnvelopeMiddleware
from app.middleware.idempotency import IdempotencyMiddleware
from app.middleware.jwt import JWTMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.events.publisher import get_redis
from app.api.v1.deps import get_session, get_session_into_request_state
from starlette.middleware.cors import CORSMiddleware

# Order of add_middleware = REVERSE of inbound order.
# Inbound: ErrorEnvelope → RequestID → CORS → RateLimit → JWT → Idempotency → route
fast_app.add_middleware(IdempotencyMiddleware)
fast_app.add_middleware(JWTMiddleware)
fast_app.add_middleware(RateLimitMiddleware, redis=get_redis())
fast_app.add_middleware(CORSMiddleware, **cors_config())
fast_app.add_middleware(RequestIDMiddleware)
fast_app.add_middleware(ErrorEnvelopeMiddleware)  # outermost

# Force every route to share its session with the idempotency middleware.
fast_app.dependency_overrides[get_session] = get_session_into_request_state
```

- [ ] **Step 2: Boot + smoke check**

```bash
cd apps/api
uv run uvicorn app.main:app --port 8001 &
sleep 3
curl -i http://localhost:8001/health  # 200, X-Request-Id header present
curl -i http://localhost:8001/v1/me  # 401 auth_missing envelope
kill %1
```

- [ ] **Step 3: Commit**

```bash
git add apps/api/app/main.py
git commit -m "feat(api): register full middleware stack with correct order + DB session override"
```

---

# Phase H — Stub endpoints + OpenAPI CI gate (Day 7)

## Task 38: `POST /v1/mood` + `POST /v1/energy`

**Files:**
- Create: `apps/api/app/schemas/mood.py` · `apps/api/app/schemas/energy.py`
- Create: `apps/api/app/api/v1/routes/mood.py` · `apps/api/app/api/v1/routes/energy.py`
- Modify: `apps/api/app/api/v1/router.py`

- [ ] **Step 1: Mood schema**

```python
"""Pydantic schemas for /v1/mood."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MoodLogCreate(BaseModel):
    score: int = Field(ge=1, le=5)
    note: str | None = Field(default=None, max_length=1000)
    logged_at: datetime | None = None


class MoodLogRead(BaseModel):
    id: UUID
    user_id: UUID
    score: int
    note: str | None
    logged_at: datetime
```

- [ ] **Step 2: Mood route**

```python
"""POST /v1/mood — stub endpoint. Behavioral event emitted to events:mood_energy."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_session, get_event_publisher
from app.db.models.mood_log import MoodLog
from app.events.streams import EventPublisher
from app.schemas.mood import MoodLogCreate, MoodLogRead
from lockin_events import MoodLogged

router = APIRouter(prefix="/v1/mood", tags=["mood"])


@router.post("", response_model=MoodLogRead, status_code=201)
async def create_mood_log(
    payload: MoodLogCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    publisher: EventPublisher = Depends(get_event_publisher),
) -> MoodLogRead:
    user_id = request.state.user_id
    row = MoodLog(
        user_id=user_id,
        score=payload.score,
        note=payload.note,
        logged_at=payload.logged_at or datetime.now(timezone.utc),
    )
    session.add(row)
    await session.flush()
    event = MoodLogged(user_id=user_id, score=row.score, logged_at=row.logged_at)
    await publisher.publish_behavioral("events:mood_energy", event)
    return MoodLogRead(
        id=row.id,
        user_id=row.user_id,
        score=row.score,
        note=row.note,
        logged_at=row.logged_at,
    )
```

- [ ] **Step 3: Energy route** — copy of mood, substituting `EnergyLogged`/`EnergyLog`/`/v1/energy`.

- [ ] **Step 4: Mount routes**

In `apps/api/app/api/v1/router.py`:
```python
from app.api.v1.routes import mood, energy
api_router.include_router(mood.router)
api_router.include_router(energy.router)
```

- [ ] **Step 5: Integration test**

```python
@pytest.mark.asyncio
async def test_post_mood_returns_201_and_emits_event(authed_client, fake_publisher):
    r = await authed_client.post("/v1/mood", json={"score": 4, "note": "ok"})
    assert r.status_code == 201
    assert fake_publisher.behavioral_calls == [("events:mood_energy", "mood.logged")]
```

- [ ] **Step 6: Commit**

```bash
git add apps/api/app/schemas/mood.py apps/api/app/schemas/energy.py apps/api/app/api/v1/routes/mood.py apps/api/app/api/v1/routes/energy.py apps/api/app/api/v1/router.py
git commit -m "feat(api): POST /v1/mood + POST /v1/energy stub endpoints (behavioral emit)"
```

## Task 39: Idempotency TTL cleanup job

**Files:**
- Create: `apps/api/app/jobs/cleanup_idempotency.py`

- [ ] **Step 1: Implement batched DELETE**

```python
"""Hourly cleanup of idempotency_keys older than 24h. Batched to avoid long locks.

Spec §4 bend #5. Pattern is reused by sync-token cleanup in §5.
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

BATCH_SIZE = 10_000


async def cleanup_idempotency_keys(session: AsyncSession) -> int:
    total = 0
    while True:
        result = await session.execute(
            text(
                "DELETE FROM idempotency_keys "
                "WHERE id IN ("
                "  SELECT id FROM idempotency_keys "
                "  WHERE created_at < now() - interval '24 hours' "
                "  LIMIT :n"
                ") RETURNING id"
            ),
            {"n": BATCH_SIZE},
        )
        deleted = len(result.fetchall())
        await session.commit()
        total += deleted
        if deleted < BATCH_SIZE:
            break
    logger.info("idempotency cleanup", total=total)
    return total
```

- [ ] **Step 2: Test (insert 100 old rows, run, assert all gone)** — write a simple integration test against the test DB.

- [ ] **Step 3: Commit**

```bash
git add apps/api/app/jobs/cleanup_idempotency.py apps/api/tests/test_cleanup_idempotency.py
git commit -m "feat(api): batched idempotency-keys TTL cleanup (10k/batch)"
```

## Task 40: OpenAPI dump script + CI diff gate

**Files:**
- Create: `apps/api/scripts/dump_openapi.py`
- Create: `packages/shared-types/openapi.json` (initial dump)
- Modify: root `package.json` (add `openapi:dump` script)
- Modify: `.github/workflows/pr.yml`

- [ ] **Step 1: Dump script**

```python
"""Dump OpenAPI to packages/shared-types/openapi.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.main import app

OUT = Path(__file__).resolve().parents[3] / "packages" / "shared-types" / "openapi.json"


def main() -> int:
    schema = app.openapi()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Root `package.json` script**

Add to `scripts`:
```json
    "openapi:dump": "cd apps/api && uv run python scripts/dump_openapi.py"
```

- [ ] **Step 3: Initial dump + commit**

```bash
pnpm openapi:dump
git add apps/api/scripts/dump_openapi.py packages/shared-types/openapi.json package.json
git commit -m "feat(api): openapi dump script + initial schema snapshot"
```

- [ ] **Step 4: CI gate in `.github/workflows/pr.yml`**

Add a new step after typecheck:
```yaml
      - name: OpenAPI schema is up to date
        run: |
          pnpm openapi:dump
          git diff --exit-code packages/shared-types/openapi.json
```

- [ ] **Step 5: Commit CI change**

```bash
git add .github/workflows/pr.yml
git commit -m "ci: fail PR if packages/shared-types/openapi.json is stale"
```

---

# Phase I — Calendar OAuth + storage + migration 0014 (Day 8a)

## Task 41: NextAuth scope extension + re-consent flag

**Files:**
- Modify: `apps/web/src/auth.ts` (extend scope)

- [ ] **Step 1: Extend the Google provider scope**

Find the Google provider config in `apps/web/src/auth.ts` and update:
```typescript
Google({
  clientId: process.env.GOOGLE_CLIENT_ID,
  clientSecret: process.env.GOOGLE_CLIENT_SECRET,
  authorization: {
    params: {
      scope: "openid email profile https://www.googleapis.com/auth/calendar.readonly",
      access_type: "offline",
      prompt: "consent",  // forces refresh_token issuance even for returning users
    },
  },
}),
```

- [ ] **Step 2: Persist refresh_token in the JWT callback** so the BFF can forward it to the api on /v1/calendar/initial_sync:

```typescript
callbacks: {
  async jwt({ token, account }) {
    if (account?.refresh_token) {
      token.googleRefreshToken = account.refresh_token;
      token.googleScopes = (account.scope ?? "").split(" ");
    }
    return token;
  },
},
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/auth.ts
git commit -m "feat(auth): extend Google scope to include calendar.readonly + persist refresh token in JWT"
```

## Task 42: `oauth_tokens` service (CRUD with envelope encryption)

**Files:**
- Create: `apps/api/app/services/oauth_token_service.py`
- Create: `apps/api/tests/test_oauth_token_service.py`

- [ ] **Step 1: Service**

```python
"""Service layer for oauth_tokens (encrypt/decrypt on the boundary)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crypto import EnvelopeCipher, KeyVersion
from app.db.models.oauth_token import OAuthToken


class OAuthTokenService:
    def __init__(self, session: AsyncSession, cipher: EnvelopeCipher) -> None:
        self._session = session
        self._cipher = cipher

    async def upsert(
        self,
        *,
        user_id: UUID,
        provider: str,
        refresh_token: str,
        access_token: str | None,
        access_token_expires_at: datetime | None,
        granted_scopes: list[str],
    ) -> OAuthToken:
        existing = (
            await self._session.execute(
                select(OAuthToken).where(
                    OAuthToken.user_id == user_id, OAuthToken.provider == provider
                )
            )
        ).scalar_one_or_none()

        rt_blob, key_version = self._cipher.encrypt(refresh_token.encode())
        at_blob = self._cipher.encrypt(access_token.encode())[0] if access_token else None

        if existing is None:
            row = OAuthToken(
                user_id=user_id,
                provider=provider,
                refresh_token_encrypted=rt_blob,
                access_token_encrypted=at_blob,
                key_version=int(key_version),
                access_token_expires_at=access_token_expires_at,
                granted_scopes=granted_scopes,
            )
            self._session.add(row)
            await self._session.flush()
            return row

        existing.refresh_token_encrypted = rt_blob
        existing.access_token_encrypted = at_blob
        existing.key_version = int(key_version)
        existing.access_token_expires_at = access_token_expires_at
        existing.granted_scopes = granted_scopes
        existing.disconnected_at = None
        existing.refresh_failure_count = 0
        await self._session.flush()
        return existing

    async def get_refresh_token(self, user_id: UUID, provider: str) -> str | None:
        row = (
            await self._session.execute(
                select(OAuthToken).where(
                    OAuthToken.user_id == user_id, OAuthToken.provider == provider
                )
            )
        ).scalar_one_or_none()
        if row is None or row.disconnected_at is not None:
            return None
        return self._cipher.decrypt(row.refresh_token_encrypted, KeyVersion(row.key_version)).decode()
```

- [ ] **Step 2: Test round-trip + rotation** (uses the cipher fixture from Task 15).

- [ ] **Step 3: Commit**

```bash
git add apps/api/app/services/oauth_token_service.py apps/api/tests/test_oauth_token_service.py
git commit -m "feat(api): OAuthTokenService with envelope-encrypted refresh tokens"
```

## Task 43: Migration `0014` — claim `apscheduler_jobs` under Alembic

**Files:**
- Create: `apps/api/alembic/versions/0014_alembic_claim_apscheduler.py`

This migration brings the APScheduler jobstore table into the Alembic chain so `alembic history` reflects reality. The table is created idempotently (`IF NOT EXISTS`) because APScheduler may have created it on a prior boot.

- [ ] **Step 1: Write migration**

```python
"""0014 — claim apscheduler_jobs under Alembic management.

APScheduler's SQLAlchemyJobStore auto-creates this table on first scheduler
start; without explicit migration it sits outside the Alembic chain.

Schema must match APScheduler's source:
  https://github.com/agronholm/apscheduler/blob/3.x/apscheduler/jobstores/sqlalchemy.py

Re-verify on any APScheduler bump.

Spec §5 self-review finding #1.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS apscheduler_jobs (
          id VARCHAR(191) PRIMARY KEY,
          next_run_time DOUBLE PRECISION,
          job_state BYTEA NOT NULL
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_apscheduler_jobs_next_run_time "
        "ON apscheduler_jobs (next_run_time);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_apscheduler_jobs_next_run_time;")
    op.execute("DROP TABLE IF EXISTS apscheduler_jobs;")
```

- [ ] **Step 2: Run chain + verify**

```bash
cd apps/api
uv run alembic upgrade head
docker exec lockin-postgres psql -U lockin -d lockin_dev -c "\d apscheduler_jobs"
uv run alembic history --verbose | head -30  # confirms 0014 in chain
```

- [ ] **Step 3: Commit**

```bash
git add apps/api/alembic/versions/0014_alembic_claim_apscheduler.py
git commit -m "feat(api): Alembic-manage apscheduler_jobs as migration 0014"
```

## Task 44: APScheduler bootstrap in FastAPI lifespan

**Files:**
- Create: `apps/api/app/jobs/scheduler.py`
- Modify: `apps/api/app/main.py` (lifespan starts/stops the scheduler)
- Modify: `apps/api/pyproject.toml` (add `apscheduler`)

- [ ] **Step 1: Add dep**

In `apps/api/pyproject.toml` dependencies:
```toml
    "apscheduler==3.10.4",
```
Then `cd apps/api && uv sync`.

- [ ] **Step 2: Scheduler module**

```python
"""APScheduler bootstrap. AsyncIOScheduler + Postgres-backed SQLAlchemyJobStore.

Spec §5: Postgres-backed jobstore survives restarts and enables a second worker
process in Week 5+ without rearchitecting.
"""

from __future__ import annotations

import logging

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings

logger = logging.getLogger(__name__)


def build_scheduler() -> AsyncIOScheduler:
    jobstore = SQLAlchemyJobStore(url=settings.DATABASE_URL_SYNC)
    scheduler = AsyncIOScheduler(jobstores={"default": jobstore}, timezone="UTC")
    return scheduler
```

- [ ] **Step 3: Wire into `main.py` lifespan**

In `lifespan()`, after `StreamRegistry.bootstrap()`:
```python
from app.jobs.scheduler import build_scheduler

scheduler = build_scheduler()
scheduler.start()
logger.info("scheduler started")
try:
    yield
finally:
    scheduler.shutdown(wait=False)
    logger.info("scheduler stopped")
```

- [ ] **Step 4: Boot + verify**

```bash
cd apps/api
uv run uvicorn app.main:app --port 8001 &
sleep 4
docker exec lockin-postgres psql -U lockin -d lockin_dev -c "SELECT count(*) FROM apscheduler_jobs;"
kill %1
```
Expected: returns 0 (no jobs scheduled yet) without error.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/jobs/scheduler.py apps/api/app/main.py apps/api/pyproject.toml apps/api/uv.lock
git commit -m "feat(api): APScheduler bootstrap (AsyncIO + Postgres jobstore) in lifespan"
```

---

# Phase J — Calendar polling sync (Day 8b)

## Task 45: Calendar sync decision log + fenced-lock module

**Files:**
- Create: `docs/decisions/2026-05-22-calendar-sync.md`
- Create: `apps/api/app/calendar/__init__.py`
- Create: `apps/api/app/calendar/lock_release.lua`
- Create: `apps/api/app/calendar/lock.py`

- [ ] **Step 1: Decision log**

```markdown
# Calendar sync: polling via APScheduler + Postgres jobstore + fenced Redis lock

**Date:** 2026-05-22
**Status:** Accepted

## Decision
P1 calendar sync is polling, 5-min cadence per connected user, staggered by
`hash(user_id) % 300s`. Driven by APScheduler `AsyncIOScheduler` with a
Postgres-backed `SQLAlchemyJobStore` (survives restarts).

Each sync job acquires a fenced Redis lock — `SET lock:calendar:{user_id}
<uuid7-token> EX 300 NX` — and releases via a Lua script that does an atomic
check-and-delete using the stored token. Google API calls are wrapped in
`asyncio.timeout(280)` (10s under the 300s lock TTL) so the release runs
before the lock expires even on a hang. The combination eliminates the
"lock expired, late job deletes someone else's lock" race.

Token refresh runs on a 60-bucket schedule (every minute, processing the
bucket whose user_ids hash to the current minute) with an
`asyncio.Semaphore(20)` cap on concurrent Google API calls.

Webhooks are a P2 conversation.
```

- [ ] **Step 2: Lock-release Lua**

```lua
-- Atomic fenced check-and-delete. KEYS[1] = lock key, ARGV[1] = token.
if redis.call('GET', KEYS[1]) == ARGV[1] then
  return redis.call('DEL', KEYS[1])
else
  return 0
end
```

- [ ] **Step 3: Lock module**

```python
"""Fenced calendar-sync lock. Spec §5 bend #3 + self-review #3."""

from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

import uuid_utils
from redis.asyncio import Redis
from redis.exceptions import NoScriptError

LOCK_TTL_S = 300
_LUA = Path(__file__).with_name("lock_release.lua").read_text()


@asynccontextmanager
async def calendar_sync_lock(redis: Redis, user_id: UUID) -> AsyncIterator[bool]:
    """Yield True if we acquired the lock; False if someone else holds it.

    Caller must enter a `while True` loop bailing on False.
    """
    key = f"lock:calendar:{user_id}"
    token = str(uuid_utils.uuid7())
    acquired = await redis.set(key, token, nx=True, ex=LOCK_TTL_S)
    if not acquired:
        yield False
        return
    try:
        yield True
    finally:
        try:
            sha = await redis.script_load(_LUA)
            try:
                await redis.evalsha(sha, 1, key, token)
            except NoScriptError:
                await redis.eval(_LUA, 1, key, token)
        except Exception:  # noqa: BLE001
            # Best-effort release; lock will expire via TTL anyway.
            pass
```

- [ ] **Step 4: Test (integration, real Redis) — two concurrent acquires, only one gets True**

In `apps/api/tests/test_calendar_sync.py`:
```python
import asyncio
import uuid

import pytest

from app.calendar.lock import calendar_sync_lock


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fenced_lock_excludes_concurrent_acquire(real_redis):
    user = uuid.uuid4()
    async def attempt():
        async with calendar_sync_lock(real_redis, user) as got:
            if got:
                await asyncio.sleep(0.1)
            return got
    results = await asyncio.gather(attempt(), attempt())
    assert sum(results) == 1  # exactly one acquired
```

- [ ] **Step 5: Run + commit**

```bash
cd apps/api
uv run pytest tests/test_calendar_sync.py::test_fenced_lock_excludes_concurrent_acquire -v -m integration
git add docs/decisions/2026-05-22-calendar-sync.md apps/api/app/calendar/ apps/api/tests/test_calendar_sync.py
git commit -m "feat(calendar): fenced Redis lock + Lua release + decision log"
```

## Task 46: `sync_calendar` job (with `asyncio.timeout(280)` + orphan pruning)

**Files:**
- Create: `apps/api/app/calendar/sync.py`
- Create: `apps/api/app/calendar/oauth.py` (Google API client wrapper)
- Create: `apps/api/app/calendar/reconcile.py` (orphan pruning)

- [ ] **Step 1: `oauth.py` — minimal Google Calendar wrapper**

```python
"""Google Calendar API wrapper. Async via httpx."""

from __future__ import annotations

from typing import Any

import httpx

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
CALENDAR_BASE = "https://www.googleapis.com/calendar/v3"


class GoogleAuthError(Exception): ...
class GoogleSyncTokenExpired(Exception): ...  # 410


async def refresh_access_token(refresh_token: str, client_id: str, client_secret: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        if resp.status_code == 401:
            raise GoogleAuthError("refresh token rejected")
        resp.raise_for_status()
        return resp.json()


async def list_events(
    access_token: str,
    *,
    sync_token: str | None = None,
    time_min: str | None = None,
    time_max: str | None = None,
) -> dict[str, Any]:
    params: dict[str, str] = {"maxResults": "250"}
    if sync_token:
        params["syncToken"] = sync_token
    else:
        if time_min:
            params["timeMin"] = time_min
        if time_max:
            params["timeMax"] = time_max
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{CALENDAR_BASE}/calendars/primary/events",
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code == 410:
            raise GoogleSyncTokenExpired()
        if resp.status_code == 401:
            raise GoogleAuthError("access token rejected")
        resp.raise_for_status()
        return resp.json()
```

- [ ] **Step 2: `reconcile.py` — orphan pruning**

```python
"""Orphan pruning after a full re-sync (spec §5 bend #2)."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from opentelemetry import metrics

logger = logging.getLogger(__name__)
_meter = metrics.get_meter(__name__)
_orphans_metric = _meter.create_counter("lockin.calendar.orphans_pruned")


async def prune_orphans(session: AsyncSession, user_id: UUID, kept_google_ids: set[str]) -> int:
    if not kept_google_ids:
        return 0
    result = await session.execute(
        text(
            "DELETE FROM calendar_events "
            "WHERE user_id = :uid AND google_event_id NOT IN :ids "
            "RETURNING id"
        ).bindparams(
            __import__("sqlalchemy").bindparam("ids", expanding=True)
        ),
        {"uid": user_id, "ids": tuple(kept_google_ids)},
    )
    pruned = len(result.fetchall())
    _orphans_metric.add(pruned, {"user_bucket": str(hash(str(user_id)) % 100)})
    if pruned:
        logger.info("calendar orphans pruned", user_id=str(user_id), pruned=pruned)
    return pruned
```

- [ ] **Step 3: `sync.py` — the job itself**

```python
"""sync_calendar: APScheduler job per user, 5min cadence.

- Acquires fenced Redis lock.
- Refreshes access token if <5min remaining.
- Inside asyncio.timeout(280), calls Google Events list.
- On 410: drops sync_token, full re-sync, prunes orphans.
- On 401: marks user as disconnected, emits calendar.disconnected, deregisters job.
- Upserts events, emits calendar.event_synced via publish_operational.
- Releases lock via Lua.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.calendar import oauth
from app.calendar.lock import calendar_sync_lock
from app.calendar.reconcile import prune_orphans
from app.core.config import settings
from app.crypto import EnvelopeCipher, KeyVersion
from app.db.models.calendar_event import CalendarEvent
from app.db.models.oauth_token import OAuthToken
from app.events.publisher import get_redis
from app.events.streams import EventPublisher
from lockin_events import CalendarDisconnected, CalendarEventSynced

logger = logging.getLogger(__name__)


async def sync_calendar(user_id: UUID, session_factory, cipher: EnvelopeCipher) -> None:
    redis = get_redis()
    try:
        async with calendar_sync_lock(redis, user_id) as acquired:
            if not acquired:
                logger.info("calendar sync skipped — lock held", user_id=str(user_id))
                return
            try:
                async with asyncio.timeout(280):
                    await _do_sync(user_id, session_factory, cipher, redis)
            except asyncio.TimeoutError:
                logger.warning("calendar sync timeout", user_id=str(user_id))
    finally:
        await redis.aclose()


async def _do_sync(user_id: UUID, session_factory, cipher: EnvelopeCipher, redis) -> None:
    async with session_factory() as session:
        row = (
            await session.execute(
                select(OAuthToken).where(
                    OAuthToken.user_id == user_id, OAuthToken.provider == "google"
                )
            )
        ).scalar_one_or_none()
        if row is None or row.disconnected_at is not None:
            return

        # Ensure access token is fresh.
        access_token = await _ensure_access_token(session, row, cipher)

        try:
            response = await oauth.list_events(access_token, sync_token=row.sync_token)
        except oauth.GoogleSyncTokenExpired:
            # Full re-sync window.
            now = datetime.now(timezone.utc)
            response = await oauth.list_events(
                access_token,
                time_min=(now - timedelta(days=7)).isoformat(),
                time_max=(now + timedelta(days=30)).isoformat(),
            )
            await _upsert_and_emit(session, user_id, response, redis)
            kept = {it["id"] for it in response.get("items", [])}
            await prune_orphans(session, user_id, kept)
            row.sync_token = response.get("nextSyncToken")
            await session.commit()
            return
        except oauth.GoogleAuthError:
            row.disconnected_at = datetime.now(timezone.utc)
            await session.commit()
            publisher = EventPublisher(redis)
            await publisher.publish_operational(
                "events:calendar",
                CalendarDisconnected(user_id=user_id, reason="auth_revoked"),
            )
            return

        await _upsert_and_emit(session, user_id, response, redis)
        row.sync_token = response.get("nextSyncToken", row.sync_token)
        if row.calendar_initial_sync_completed_at is None:
            row.calendar_initial_sync_completed_at = datetime.now(timezone.utc)
        await session.commit()


async def _ensure_access_token(session: AsyncSession, row: OAuthToken, cipher: EnvelopeCipher) -> str:
    now = datetime.now(timezone.utc)
    if (
        row.access_token_encrypted is not None
        and row.access_token_expires_at is not None
        and row.access_token_expires_at - now > timedelta(minutes=5)
    ):
        return cipher.decrypt(row.access_token_encrypted, KeyVersion(row.key_version)).decode()

    refresh_token = cipher.decrypt(row.refresh_token_encrypted, KeyVersion(row.key_version)).decode()
    refreshed = await oauth.refresh_access_token(
        refresh_token, settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET
    )
    access = refreshed["access_token"]
    expires_in = int(refreshed.get("expires_in", 3600))
    row.access_token_encrypted = cipher.encrypt(access.encode())[0]
    row.access_token_expires_at = now + timedelta(seconds=expires_in - 30)
    return access


async def _upsert_and_emit(session: AsyncSession, user_id: UUID, response: dict, redis) -> None:
    items = response.get("items", [])
    publisher = EventPublisher(redis)
    for item in items:
        starts = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
        ends = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")
        if starts is None or ends is None:
            continue
        stmt = pg_insert(CalendarEvent).values(
            user_id=user_id,
            google_event_id=item["id"],
            summary=item.get("summary"),
            starts_at=starts,
            ends_at=ends,
            etag=item.get("etag"),
            source_calendar_id="primary",
        ).on_conflict_do_update(
            index_elements=["user_id", "google_event_id"],
            set_={
                "summary": item.get("summary"),
                "starts_at": starts,
                "ends_at": ends,
                "etag": item.get("etag"),
                "updated_at": datetime.now(timezone.utc),
            },
        )
        await session.execute(stmt)
        await publisher.publish_operational(
            "events:calendar",
            CalendarEventSynced(user_id=user_id, google_event_id=item["id"]),
        )
```

- [ ] **Step 4: Tests — 410 prunes orphans, 401 marks disconnected, lock prevents concurrent runs** (each mocks `oauth.list_events` with the appropriate exception/payload).

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/calendar/oauth.py apps/api/app/calendar/reconcile.py apps/api/app/calendar/sync.py apps/api/tests/test_calendar_sync.py
git commit -m "feat(calendar): sync_calendar job with timeout, 410 orphan prune, 401 disconnect"
```

## Task 47: Token refresh job (60-bucket partition + `Semaphore(20)`)

**Files:**
- Create: `apps/api/app/jobs/refresh_tokens.py`

- [ ] **Step 1: Implement**

```python
"""Hourly-buckets token refresh. Spec §5 bend #4.

Runs every minute. Processes only users whose user_id hashes to the current
minute (60 buckets). Caps outbound Google API calls at 20 concurrent.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.calendar import oauth
from app.core.config import settings
from app.crypto import EnvelopeCipher, KeyVersion
from app.db.models.oauth_token import OAuthToken

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 20


async def refresh_tokens_bucket(session_factory, cipher: EnvelopeCipher) -> int:
    minute = datetime.now(timezone.utc).minute
    threshold = datetime.now(timezone.utc) + timedelta(hours=24)
    async with session_factory() as session:
        rows = (
            await session.execute(
                text(
                    "SELECT id FROM oauth_tokens "
                    "WHERE disconnected_at IS NULL "
                    "AND access_token_expires_at < :threshold "
                    "AND abs(hashtext(user_id::text)) % 60 = :minute"
                ),
                {"threshold": threshold, "minute": minute},
            )
        ).all()
        ids = [r[0] for r in rows]

    if not ids:
        return 0

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    refreshed = 0

    async def _refresh_one(token_id):
        nonlocal refreshed
        async with semaphore, session_factory() as s:
            row = await s.get(OAuthToken, token_id)
            if row is None or row.disconnected_at is not None:
                return
            try:
                refresh_token = cipher.decrypt(
                    row.refresh_token_encrypted, KeyVersion(row.key_version)
                ).decode()
                payload = await oauth.refresh_access_token(
                    refresh_token, settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET
                )
                row.access_token_encrypted = cipher.encrypt(payload["access_token"].encode())[0]
                row.access_token_expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=int(payload.get("expires_in", 3600)) - 30
                )
                row.refresh_failure_count = 0
                await s.commit()
                refreshed += 1
            except Exception:  # noqa: BLE001
                row.refresh_failure_count += 1
                await s.commit()
                logger.warning("token refresh failed", token_id=str(token_id))

    await asyncio.gather(*(_refresh_one(i) for i in ids))
    return refreshed
```

- [ ] **Step 2: Register the bucket job in `main.py` lifespan** (every minute):

```python
from app.jobs.refresh_tokens import refresh_tokens_bucket
from app.crypto import EnvelopeCipher
from app.db.session import async_session_factory

cipher = EnvelopeCipher.from_env(prefix="OAUTH_TOKEN_ENCRYPTION_KEY")
scheduler.add_job(
    refresh_tokens_bucket,
    "cron",
    minute="*",
    args=[async_session_factory, cipher],
    id="oauth_token_refresh_bucket",
    replace_existing=True,
)
```

- [ ] **Step 3: Commit**

```bash
git add apps/api/app/jobs/refresh_tokens.py apps/api/app/main.py
git commit -m "feat(calendar): per-minute bucket-partitioned token refresh with Semaphore(20)"
```

## Task 48: Reaper + idempotency-cleanup jobs registered

**Files:**
- Modify: `apps/api/app/main.py`

- [ ] **Step 1: Register both as scheduled jobs**

In `main.py` next to the refresh-tokens job:
```python
from app.jobs.reaper import Reaper
from app.jobs.cleanup_idempotency import cleanup_idempotency_keys

reaper = Reaper(get_redis())

async def _reaper_sweep():
    await reaper.sweep_once()

async def _idempotency_sweep():
    async with async_session_factory() as session:
        await cleanup_idempotency_keys(session)

scheduler.add_job(_reaper_sweep, "interval", seconds=60, id="reaper", replace_existing=True)
scheduler.add_job(_idempotency_sweep, "cron", minute=0, id="idempotency_cleanup", replace_existing=True)
```

- [ ] **Step 2: Boot + verify both jobs land in apscheduler_jobs**

```bash
cd apps/api
uv run uvicorn app.main:app --port 8001 &
sleep 4
docker exec lockin-postgres psql -U lockin -d lockin_dev -c "SELECT id, next_run_time FROM apscheduler_jobs;"
kill %1
```
Expected: 3 rows (reaper, idempotency_cleanup, oauth_token_refresh_bucket).

- [ ] **Step 3: Commit**

```bash
git add apps/api/app/main.py
git commit -m "feat(api): scheduled reaper (60s) + idempotency cleanup (hourly)"
```

---

# Phase K — Calendar UX + tests (Day 9)

## Task 49: SSE endpoint for initial-sync status

**Files:**
- Create: `apps/api/app/api/v1/routes/integrations.py`
- Modify: `apps/api/pyproject.toml` (add `sse-starlette`)
- Modify: `apps/api/app/api/v1/router.py`

- [ ] **Step 1: Add `sse-starlette` dep**

```toml
    "sse-starlette==2.1.3",
```
Then `uv sync`.

- [ ] **Step 2: SSE endpoint + `/v1/calendar/initial_sync` POST**

```python
"""Integrations endpoints: initial sync trigger, SSE status, current state."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.v1.deps import get_session
from app.db.models.oauth_token import OAuthToken

router = APIRouter(prefix="/v1/me/integrations", tags=["integrations"])
calendar_router = APIRouter(prefix="/v1/calendar", tags=["calendar"])


@router.get("")
async def get_integrations(request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    user_id = request.state.user_id
    row = (
        await session.execute(
            select(OAuthToken).where(OAuthToken.user_id == user_id, OAuthToken.provider == "google")
        )
    ).scalar_one_or_none()
    return {
        "google_calendar": {
            "connected": row is not None and row.disconnected_at is None,
            "scopes": row.granted_scopes if row else [],
            "initial_sync_completed_at": row.calendar_initial_sync_completed_at if row else None,
        }
    }


@router.get("/sync_status")
async def sync_status(request: Request, session: AsyncSession = Depends(get_session)) -> EventSourceResponse:
    user_id = request.state.user_id

    async def event_stream():
        yield {"event": "status", "data": json.dumps({"phase": "started"})}
        # Poll the oauth_tokens row every 2s; emit phase transitions; cap at 180s.
        deadline = datetime.now(timezone.utc).timestamp() + 180
        last_phase = "started"
        while datetime.now(timezone.utc).timestamp() < deadline:
            await asyncio.sleep(2)
            async with session.begin():
                row = (
                    await session.execute(
                        select(OAuthToken).where(
                            OAuthToken.user_id == user_id, OAuthToken.provider == "google"
                        )
                    )
                ).scalar_one_or_none()
            if row is None:
                yield {"event": "status", "data": json.dumps({"phase": "failed", "reason": "no_token"})}
                return
            if row.disconnected_at is not None:
                yield {"event": "status", "data": json.dumps({"phase": "failed", "reason": "disconnected"})}
                return
            if row.calendar_initial_sync_completed_at is not None:
                yield {"event": "status", "data": json.dumps({"phase": "completed"})}
                return
            if last_phase == "started":
                last_phase = "fetching_events"
                yield {"event": "status", "data": json.dumps({"phase": "fetching_events"})}
        yield {"event": "status", "data": json.dumps({"phase": "failed", "reason": "timeout"})}

    return EventSourceResponse(event_stream())


@calendar_router.post("/initial_sync", status_code=202)
async def initial_sync(request: Request) -> dict:
    """Schedules sync_calendar to run immediately for the requesting user."""
    user_id = request.state.user_id
    from app.calendar.sync import sync_calendar
    from app.crypto import EnvelopeCipher
    from app.db.session import async_session_factory
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler: AsyncIOScheduler = request.app.state.scheduler  # set in main.py
    cipher = EnvelopeCipher.from_env(prefix="OAUTH_TOKEN_ENCRYPTION_KEY")
    scheduler.add_job(
        sync_calendar,
        args=[user_id, async_session_factory, cipher],
        id=f"initial_calendar_sync_{user_id}",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )
    return {"status": "queued"}
```

- [ ] **Step 3: Mount routers + expose scheduler on app.state**

In `main.py`'s `lifespan`, after building the scheduler: `fast_app.state.scheduler = scheduler`. In `router.py`:
```python
from app.api.v1.routes import integrations
api_router.include_router(integrations.router)
api_router.include_router(integrations.calendar_router)
```

- [ ] **Step 4: Commit**

```bash
git add apps/api/app/api/v1/routes/integrations.py apps/api/app/api/v1/router.py apps/api/app/main.py apps/api/pyproject.toml apps/api/uv.lock
git commit -m "feat(calendar): SSE sync_status + POST /v1/calendar/initial_sync"
```

## Task 50: Frontend SSE consumer (Bearer-compatible)

**Files:**
- Create: `apps/web/src/lib/sync-status.ts`
- Modify: `apps/web/package.json` (add `@microsoft/fetch-event-source`)

- [ ] **Step 1: Add dep**

```bash
cd apps/web
pnpm add @microsoft/fetch-event-source
```

- [ ] **Step 2: Consumer**

```typescript
"""Browser EventSource cannot carry Authorization headers — see spec §5 self-review #2."""
import { fetchEventSource } from "@microsoft/fetch-event-source";

export type SyncPhase = "started" | "fetching_events" | "events_received" | "completed" | "failed";
export interface SyncStatusUpdate { phase: SyncPhase; reason?: string; count?: number }

export async function subscribeSyncStatus(
  apiUrl: string,
  bearer: string,
  onUpdate: (u: SyncStatusUpdate) => void,
  signal: AbortSignal,
): Promise<void> {
  await fetchEventSource(`${apiUrl}/v1/me/integrations/sync_status`, {
    headers: { Authorization: `Bearer ${bearer}` },
    signal,
    onmessage(ev) {
      if (ev.event !== "status") return;
      try {
        onUpdate(JSON.parse(ev.data) as SyncStatusUpdate);
      } catch {/* malformed; ignore */}
    },
    onerror() { /* fetchEventSource will retry; we let it */ },
  });
}
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/lib/sync-status.ts apps/web/package.json pnpm-lock.yaml
git commit -m "feat(web): SSE consumer for /sync_status using @microsoft/fetch-event-source"
```

## Task 51: Settings/integrations page wires connect + SSE

**Files:**
- Modify: `apps/web/src/app/(authed)/settings/integrations/page.tsx`
- Create: `apps/web/src/app/api/integrations/route.ts` (BFF proxy)
- Create: `apps/web/src/app/api/calendar/initial_sync/route.ts` (BFF proxy)

- [ ] **Step 1: BFF routes** — same shape as `apps/web/src/app/api/tasks/route.ts` from Slice 0; forward Bearer.

- [ ] **Step 2: Integrations page wires React Query + SSE**

```tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Button, EmptyState, Banner } from "@lockin/ui";
import { subscribeSyncStatus, type SyncStatusUpdate } from "@/lib/sync-status";

export default function IntegrationsPage() {
  const { data } = useQuery({
    queryKey: ["integrations"],
    queryFn: async () => (await fetch("/api/integrations")).json(),
  });
  const [status, setStatus] = useState<SyncStatusUpdate | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("just_connected") !== "calendar") return;
    const controller = new AbortController();
    fetch("/api/calendar/initial_sync", { method: "POST" });
    subscribeSyncStatus("/api", "BFF-FORWARDED", setStatus, controller.signal);
    return () => controller.abort();
  }, []);

  const connected = data?.google_calendar?.connected;
  return (
    <section>
      <h1>Integrations</h1>
      {connected ? (
        <p>Google Calendar connected.</p>
      ) : (
        <EmptyState
          title="Connect Google Calendar"
          body="LockIn reads your calendar to schedule around real meetings."
          action={{ label: "Connect", onClick: () => { window.location.href = "/api/auth/signin/google?callbackUrl=/settings/integrations?just_connected=calendar"; } }}
        />
      )}
      {status?.phase === "fetching_events" && <Banner>Calendar sync in progress…</Banner>}
      {status?.phase === "failed" && <Banner tone="warning">Sync failed: {status.reason}</Banner>}
    </section>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/app/\(authed\)/settings/integrations/page.tsx apps/web/src/app/api/integrations/route.ts apps/web/src/app/api/calendar/initial_sync/route.ts
git commit -m "feat(web): /settings/integrations connect flow + SSE sync status banner"
```

## Task 52: Five calendar sync tests

**Files:**
- Modify: `apps/api/tests/test_calendar_sync.py`

- [ ] **Step 1: Add the four remaining tests** (lock test was in Task 45):

```python
@pytest.mark.asyncio
async def test_initial_sync_persists_14_day_window(monkeypatch, test_session, cipher):
    # Mock oauth.list_events to return 5 events spanning -7d to +30d; verify rows.
    ...

@pytest.mark.asyncio
async def test_incremental_sync_uses_sync_token(monkeypatch, test_session, cipher):
    # First call: no sync_token in args; second call: sync_token passed.
    ...

@pytest.mark.asyncio
async def test_410_triggers_full_resync_and_prunes_orphans(monkeypatch, test_session, cipher):
    # Pre-populate calendar_events with 3 rows; mock 410 then a full-sync response
    # containing only 2 of those google_event_ids; assert orphan deleted.
    ...

@pytest.mark.asyncio
async def test_401_marks_disconnected_and_emits_event(monkeypatch, test_session, cipher):
    # Mock list_events to raise GoogleAuthError; assert disconnected_at set and
    # calendar.disconnected published once.
    ...
```

(Stub these fully when implementing; the structure above is enough to write them top-down.)

- [ ] **Step 2: Run + commit**

```bash
cd apps/api
uv run pytest tests/test_calendar_sync.py -v
git add apps/api/tests/test_calendar_sync.py
git commit -m "test(calendar): 4 sync semantics tests (initial, incremental, 410, 401)"
```

## Task 53: Calendar carry-forward debt + runbook

**Files:**
- Create: `docs/decisions/2026-05-22-carry-forward-debt.md`
- Create: `docs/runbooks/oauth-token-encryption-key-rotation.md`

- [ ] **Step 1: Carry-forward debt decision log**

```markdown
# Week 3-4 carry-forward debt

**Date:** 2026-05-22
**Status:** Accepted (debt incurred deliberately)

| Debt | Trigger |
|---|---|
| Transactional outbox for event-emitting mutations | Before any deploy where api runs more than one instance, OR before staging cutover, whichever comes first. Local single-process dev is exempt. |
| MCP `app` package-name collision (apps/api + apps/mcp both install as `app`) | Next slice that touches `apps/mcp/` for non-trivial work. |
| Calendar webhooks (push notifications) | P2 conversation (out of scope for P1). |
| On-device Whisper for voice capture | P2. |

These are scaffolding compromises, not bugs. Do not "just fix" them out of cycle —
the triggers exist so the fix happens at the right scope.
```

- [ ] **Step 2: Rotation runbook**

```markdown
# Runbook: OAuth Token Encryption Key Rotation

**Purpose:** Rotate the AES-GCM key that encrypts OAuth refresh tokens in
`oauth_tokens.refresh_token_encrypted`. Zero-downtime via versioned keys.

## Trigger
- Scheduled annual rotation (set calendar reminder)
- Suspected key compromise
- Compliance event

## Steps
1. Generate the new key:
   ```
   openssl rand -hex 32
   ```
2. Deploy `OAUTH_TOKEN_ENCRYPTION_KEY_V<N+1>=<hex>` to all environments
   alongside the existing `_V<N>`. Restart api pods so they load both.
3. Run the re-encrypt job (one-shot script — implement in the slice that
   first needs to rotate; trivial loop over `oauth_tokens` rows).
4. Verify `SELECT min(key_version), max(key_version) FROM oauth_tokens`
   returns `(N+1, N+1)`.
5. Remove `OAUTH_TOKEN_ENCRYPTION_KEY_V<N>` from env.
6. Restart api pods.

## Failure modes
- Step 3 partial completion: safe to re-run; idempotent on `key_version`.
- Skipping step 4 then doing step 5: rows still encrypted with V<N> become
  permanently undecryptable. Always verify before removing the old key.
```

- [ ] **Step 3: Commit**

```bash
git add docs/decisions/2026-05-22-carry-forward-debt.md docs/runbooks/oauth-token-encryption-key-rotation.md
git commit -m "docs: Week 3-4 carry-forward debt + OAuth key rotation runbook"
```

---

# Phase L — Frontend integration (Day 10 AM)

## Task 54: Wire `sanitize_next_param` into `middleware.ts`

**Files:**
- Modify: `apps/web/src/middleware.ts`

- [ ] **Step 1: Rewrite the middleware**

```typescript
import { auth } from "@/auth";
import { NextResponse } from "next/server";
import { sanitizeNextParam } from "@/lib/auth/redirect";

const ANONYMOUS = new Set(["/login", "/api/auth", "/api/health", "/_next", "/favicon.ico"]);

export default auth((req) => {
  const path = req.nextUrl.pathname;
  const isStatic = ANONYMOUS.has(path) || [...ANONYMOUS].some((p) => path.startsWith(p));
  if (isStatic) return;

  if (!req.auth) {
    const next = sanitizeNextParam(path);
    return NextResponse.redirect(new URL(`/login?next=${encodeURIComponent(next)}`, req.nextUrl.origin));
  }

  if (path === "/login") {
    const requested = sanitizeNextParam(req.nextUrl.searchParams.get("next"));
    return NextResponse.redirect(new URL(requested, req.nextUrl.origin));
  }
});

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
```

- [ ] **Step 2: Commit**

```bash
git add apps/web/src/middleware.ts
git commit -m "feat(web): auth middleware uses sanitize_next_param (open-redirect safe)"
```

## Task 55: Theme cookie + Accept-CH hint + Secure flag

**Files:**
- Modify: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/components/theme/ThemeToggle.tsx`

- [ ] **Step 1: layout.tsx — server-side theme decision**

```tsx
import type { ReactNode } from "react";
import { cookies, headers } from "next/headers";
import "./globals.css";

function resolveTheme(): "light" | "dark" | null {
  const cookieTheme = cookies().get("theme")?.value;
  if (cookieTheme === "dark" || cookieTheme === "light") return cookieTheme;
  const hint = headers().get("Sec-CH-Prefers-Color-Scheme");
  if (hint === "dark") return "dark";
  if (hint === "light") return "light";
  return null;
}

export default function RootLayout({ children }: { children: ReactNode }) {
  const theme = resolveTheme();
  return (
    <html lang="en" className={theme ?? ""}>
      <head>
        <meta httpEquiv="Accept-CH" content="Sec-CH-Prefers-Color-Scheme" />
      </head>
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 2: ThemeToggle**

```tsx
"use client";
import { useState } from "react";

export function ThemeToggle({ initial }: { initial: "light" | "dark" | null }) {
  const [theme, setTheme] = useState<"light" | "dark">(initial ?? "light");

  function flip() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.classList.remove("light", "dark");
    document.documentElement.classList.add(next);
    localStorage.setItem("theme", next);
    const secure = process.env.NODE_ENV === "production" ? "; Secure" : "";
    document.cookie = `theme=${next}; Path=/; Max-Age=${31536000}; SameSite=Lax${secure}`;
  }

  return (
    <button type="button" onClick={flip} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}>
      {theme === "dark" ? "🌙" : "☀️"}
    </button>
  );
}
```

- [ ] **Step 3: Configure Tailwind class-based dark mode**

In `apps/web/tailwind.config.ts`, ensure `darkMode: "class"`.

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/app/layout.tsx apps/web/src/components/theme apps/web/tailwind.config.ts
git commit -m "feat(web): theme cookie + Sec-CH-Prefers-Color-Scheme fallback (no flash)"
```

## Task 56: FAB wired to capture palette + focus-return test

**Files:**
- Modify: `apps/web/src/app/(authed)/today/page.tsx` (mount FAB + palette dialog)
- Modify: `apps/web/src/app/(authed)/layout.tsx` (FAB visible on mobile only via component's md:hidden)
- Modify: an existing palette component from Slice 0 (wrap in Radix Dialog if not already)
- Modify: `apps/web/package.json` (add `@radix-ui/react-dialog` if absent)

- [ ] **Step 1: Wrap palette in Radix Dialog with default `onOpenAutoFocus` + `onCloseAutoFocus`** (focus return is Radix's default — verify by reading current palette source).

- [ ] **Step 2: Add focus-return test**

```typescript
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import TodayPage from "@/app/(authed)/today/page";

describe("Today page palette focus management", () => {
  it("returns focus to trigger when palette closes", async () => {
    render(<TodayPage />);
    const trigger = screen.getByRole("button", { name: /open palette/i });
    trigger.focus();
    fireEvent.click(trigger);
    // Palette opens; first input gets focus.
    const input = await screen.findByRole("textbox");
    expect(document.activeElement).toBe(input);
    // Close via Escape.
    fireEvent.keyDown(input, { key: "Escape" });
    expect(document.activeElement).toBe(trigger);
  });
});
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/app/\(authed\)/today/ apps/web/src/app/\(authed\)/layout.tsx apps/web/src/components/palette apps/web/package.json pnpm-lock.yaml apps/web/src/tests
git commit -m "feat(web): FAB opens palette; focus returns to trigger on close"
```

## Task 57: BFF DELETE `/api/tasks/[id]` (replaces `?id=` query-param debt)

**Files:**
- Create: `apps/web/src/app/api/tasks/[id]/route.ts`
- Delete: `?id=` query handling from `apps/web/src/app/api/tasks/route.ts`
- Modify: `apps/web/src/hooks/use-task-mutations.ts` (or wherever DELETE is called)

- [ ] **Step 1: New segment route**

```typescript
import { auth } from "@/auth";
import { NextRequest, NextResponse } from "next/server";

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const session = await auth();
  if (!session?.user) return NextResponse.json({ error: "auth_missing" }, { status: 401 });
  const { id } = await params;
  const upstream = await fetch(`${process.env.API_URL}/v1/tasks/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${(session as any).bearerToken}`,
      "Idempotency-Key": req.headers.get("Idempotency-Key") ?? crypto.randomUUID(),
    },
  });
  if (!upstream.ok) {
    return NextResponse.json({ error: "upstream_error" }, { status: upstream.status });
  }
  return new Response(null, { status: 204 });
}
```

- [ ] **Step 2: Strip the `?id=` branch from the old route handler.**

- [ ] **Step 3: Update the React Query mutation hook to call `/api/tasks/${id}` (no query string).**

- [ ] **Step 4: Run Slice 0 deletion tests** — they should still pass against the new shape.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/app/api/tasks/ apps/web/src/hooks
git commit -m "refactor(web): DELETE /api/tasks/[id] segment replaces ?id= query (debt D resolved)"
```

---

# Phase M — DoD, smoke test, handoff (Day 10 PM)

## Task 58: vitest-axe a11y test for every empty-state route

**Files:**
- Create: `apps/web/src/tests/a11y.test.tsx`
- Modify: `apps/web/package.json` (add `vitest-axe`)

- [ ] **Step 1: Add dep**

```bash
cd apps/web
pnpm add -D vitest-axe
```

- [ ] **Step 2: Test**

```typescript
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { axe } from "vitest-axe";

import TodayPage from "@/app/(authed)/today/page";
import SchedulePage from "@/app/(authed)/schedule/page";
import SettingsPage from "@/app/(authed)/settings/page";
import IntegrationsPage from "@/app/(authed)/settings/integrations/page";

describe.each([
  ["/today", TodayPage],
  ["/schedule", SchedulePage],
  ["/settings", SettingsPage],
  ["/settings/integrations", IntegrationsPage],
])("axe-clean: %s", (_path, Page) => {
  it("has zero violations", async () => {
    const { container } = render(<Page />);
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });
});
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/tests/a11y.test.tsx apps/web/package.json pnpm-lock.yaml
git commit -m "test(web): vitest-axe asserts zero a11y violations on every authed route"
```

## Task 59: Lighthouse CI per-category gates

**Files:**
- Create: `.lighthouserc.json`
- Modify: `.github/workflows/pr.yml`
- Modify: root `package.json` (add `lighthouse` script)

- [ ] **Step 1: `.lighthouserc.json`**

```json
{
  "ci": {
    "collect": {
      "url": ["http://localhost:3000/today", "http://localhost:3000/schedule", "http://localhost:3000/settings"],
      "numberOfRuns": 1
    },
    "assert": {
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.85 }],
        "categories:accessibility": ["error", { "minScore": 0.95 }],
        "categories:best-practices": ["error", { "minScore": 0.90 }],
        "categories:seo": ["error", { "minScore": 0.90 }]
      }
    }
  }
}
```

- [ ] **Step 2: Root `package.json` script**

```json
    "lighthouse": "lhci autorun"
```

- [ ] **Step 3: CI step** — after the web build in `.github/workflows/pr.yml`, add a job step that boots `pnpm --filter @lockin/web start` in the background and runs `pnpm lighthouse`. (Adjust to match the existing CI workflow style.)

- [ ] **Step 4: Commit**

```bash
git add .lighthouserc.json package.json .github/workflows/pr.yml
git commit -m "ci: Lighthouse per-category gates (a11y 0.95, perf 0.85, best/seo 0.90)"
```

## Task 60: EXPLAIN snapshots + schema diagram

**Files:**
- Create: `docs/architecture/explain-snapshots.md`
- Create: `docs/architecture/schema-w3-4.svg`
- Create: `apps/api/scripts/dump_schema.py`
- Modify: root `package.json` (add `schema:dump` script)

- [ ] **Step 1: EXPLAIN snapshots**

Run against the seeded DB and capture output:
```bash
docker exec lockin-postgres psql -U lockin -d lockin_dev -c \
  "EXPLAIN ANALYZE SELECT * FROM tasks WHERE user_id='00000000-0000-0000-0000-000000000001' ORDER BY created_at DESC, id DESC LIMIT 20;" > /tmp/tasks_explain.txt
# repeat for mood_logs, calendar_events
```
Paste into `docs/architecture/explain-snapshots.md` with section per query, asserting "Index Scan" appears.

- [ ] **Step 2: Schema dump script**

```python
"""Render an ER diagram of the SQLAlchemy models to SVG."""

from __future__ import annotations

from pathlib import Path
import eralchemy2

from app.db.base import Base
import app.db.models  # noqa: F401 — registers models on metadata

OUT = Path(__file__).resolve().parents[3] / "docs" / "architecture" / "schema-w3-4.svg"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    eralchemy2.render_er(Base.metadata, str(OUT))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
```

Add `eralchemy2` to `[project.optional-dependencies] dev` in pyproject.

- [ ] **Step 3: Generate the diagram**

```bash
pnpm schema:dump
```

- [ ] **Step 4: Commit**

```bash
git add apps/api/scripts/dump_schema.py docs/architecture/ package.json apps/api/pyproject.toml apps/api/uv.lock
git commit -m "docs(arch): EXPLAIN snapshots + auto-generated schema diagram"
```

## Task 61: Smoke test script + execution

**Files:**
- Create: `docs/handoffs/week-3-4-smoke-test.md`

- [ ] **Step 1: Write the smoke test script (verbatim from spec §7 bend #3)**

```markdown
# Week 3-4 Scaffolding Smoke Test

**Run on:** Day 10 against local-first substrate (Docker pg16+timescale, redis, api, web).
**Doubles as:** Week 5-6 regression checklist before they start.
**Pre-conditions:** All services up; `OAUTH_TOKEN_ENCRYPTION_KEY_V1` set; a Google test
account with calendar access; a fresh user has not yet signed in.

## Steps

1. Open `http://localhost:3000/`. Expect: redirect to `/login`.
2. Click "Sign in with Google", complete OAuth. Expect: redirect to `/today` with the
   "Capture your first task" empty state.
3. Navigate to `/settings/integrations`. Expect: "Connect Google Calendar" button visible.
4. Click "Connect". Complete the OAuth consent. Expect: redirect to
   `/settings/integrations?just_connected=calendar`. The SSE banner shows
   "Calendar sync in progress…" then disappears within 60s.
5. Verify in Postgres:
   ```
   SELECT count(*) FROM oauth_tokens WHERE provider='google'; -- 1
   SELECT key_version, granted_scopes FROM oauth_tokens; -- 1, contains calendar.readonly
   SELECT count(*) FROM calendar_events; -- > 0
   ```
6. POST a task via the BFF:
   ```
   curl -X POST http://localhost:3000/api/tasks \
     -H 'Idempotency-Key: smoke-abc123' \
     -H 'Content-Type: application/json' \
     -d '{"title":"smoke task"}'
   ```
   Expect: 201, body contains a v7 UUID. Verify: `SELECT id FROM tasks ORDER BY created_at DESC LIMIT 1;` returns the same UUID. Verify: `XLEN events:tasks` increased by 1.
7. Repeat the same POST with the same key + body. Expect: 201, identical body, no new row.
   Verify: `SELECT count(*) FROM tasks WHERE title='smoke task';` returns 1.
8. Repeat with the same key but `{"title":"different"}`. Expect: 422 `idempotency_key_reused`.
9. Verify: `XLEN events:tasks:dlq:capture-svc` returns 0.
10. Force Redis down: `docker compose -f infra/dev/docker-compose.yml stop redis`. Repeat
    POST `/api/tasks` with a new idempotency key. Expect: 200/201 (rate-limit fails open).
    Restart Redis: `docker compose -f infra/dev/docker-compose.yml start redis`.
11. Run `pnpm lighthouse` against `/today`. Expect: all four category gates pass.

## Pass criteria
Every step matches its expected outcome. Any failure is a slice blocker.
```

- [ ] **Step 2: Execute the smoke test manually and check off each step.**

- [ ] **Step 3: Commit**

```bash
git add docs/handoffs/week-3-4-smoke-test.md
git commit -m "docs(handoff): Week 3-4 end-to-end smoke test (Day 10 DoD gate)"
```

## Task 62: Handoff doc + CURRENT_SLICE + onboarding-deferred + final review

**Files:**
- Create: `docs/handoffs/week-3-4.md`
- Create: `docs/decisions/2026-05-22-onboarding-deferred.md`
- Modify: `docs/CURRENT_SLICE.md`

- [ ] **Step 1: Onboarding-deferred decision log**

```markdown
# P1 has no /onboarding route — empty states are the onboarding

**Date:** 2026-05-22
**Status:** Accepted

## Decision
The `/onboarding` route is not built in P1. New users land on `/today` after
OAuth completion; the "Capture your first task" empty state IS the onboarding.

## Why
A placeholder /onboarding renders worse than no route at all (broken first
impression). The PRD's 90-second onboarding target is achieved via OAuth +
first capture; adding a dedicated route that does nothing useful slows users
down. Route deferred to P2 when there's actual onboarding content to render.
```

- [ ] **Step 2: Handoff doc**

```markdown
# Week 3-4 Scaffolding — Handoff to Week 5-6

**Slice status:** ✅ Complete · merged via PR #N on 2026-06-05
**Driving spec:** docs/superpowers/specs/2026-05-22-week-3-4-scaffolding-design.md
**Driving plan:** docs/superpowers/plans/2026-05-22-week-3-4-scaffolding.md

## What shipped
- 11 new tables (migrations 0004-0014); standard row shape codified in BaseEntityMixin
- TimescaleDB hypertable behavior_events + 2 continuous aggregates
- 4 Redis streams + 8 DLQ streams + 4 consumer groups (no consumers running yet)
- Full middleware stack: ErrorEnvelope outermost, RequestID, CORS, RateLimit (fixed-window Lua), JWT (strict-Bearer with structured codes), Idempotency (2xx/4xx only, joins route txn)
- Google Calendar read-only polling sync (5min cadence, fenced lock + asyncio.timeout(280), 410 prunes orphans, 401 disconnects)
- Frontend shell: route groups, sidebar+FAB+bottom-tab nav, theme cookie with CH-hint fallback, empty states on every route, palette focus-return wired
- OpenAPI CI gate; Lighthouse CI with per-category thresholds; vitest-axe on every route

## What Week 5-6 inherits
1. `POST /v1/tasks`, `POST /v1/mood`, `POST /v1/energy` — all idempotency-aware, all
   emit via `publish_behavioral`. To wire consumers: register a consumer that reads
   from the stream, calls `BehaviorEvent.upsert(...)`, acks. DLQ + dedup pattern
   already specified.
2. `calendar_events` populated for connected users; end-to-end ingestion proven.
3. `/today` has an empty state + FAB that opens the Slice 0 palette; just swap empty
   state for populated list when tasks exist.
4. `<MoodEnergySlot>` placeholder in `(authed)/layout.tsx` — replace with real widget.
5. Storybook contains every empty state + the shell.
6. React Query + BFF route pattern reusable (`/api/mood`, `/api/energy` lift from
   `/api/tasks`).

## Three failure modes carried forward (with triggers)
| Debt | Trigger |
|---|---|
| Transactional outbox | Before any deploy where api runs >1 instance, OR staging cutover |
| MCP `app` namespace collision | Next slice that touches apps/mcp/ for non-trivial work |
| Calendar webhooks (push) | P2 conversation |

## Smoke test
See docs/handoffs/week-3-4-smoke-test.md. Re-run before starting Week 5-6 work to
confirm the spine is intact.
```

- [ ] **Step 3: Update CURRENT_SLICE.md**

Replace with:
```markdown
# Current Slice — Week 5-6 Capture Loop

> **✅ Week 3-4 Scaffolding complete (2026-06-05):** Schema spine + event streams +
> middleware + calendar sync + frontend shell.
> Handoff: [`docs/handoffs/week-3-4.md`](handoffs/week-3-4.md).

**Status:** Ready to start
**Est. duration:** TBD (handoff coming from Md)

## The Goal
Wire the capture loop: voice + text task input, mood/energy widget, notification
permission flow, real event instrumentation flowing from POST endpoints through
streams into the behavior_events hypertable.

---
*Update this file when the slice ships. Archive previous slices in docs/slices/.*
```

- [ ] **Step 4: Commit + final review against DoD**

```bash
git add docs/handoffs/week-3-4.md docs/decisions/2026-05-22-onboarding-deferred.md docs/CURRENT_SLICE.md
git commit -m "docs(handoff): Week 3-4 done — handoff to Week 5-6, CURRENT_SLICE updated"
```

- [ ] **Step 5: DoD walkthrough**

Open the spec's §7 DoD checklist and verify every row passes. Any unchecked item must be either fixed or explicitly flagged in `docs/handoffs/week-3-4.md` as a Week 5-6 blocker.

- [ ] **Step 6: Push branch, open PR with the DoD as the PR description**

```bash
git push -u origin feat/week-3-4-scaffolding
gh pr create --title "feat(week-3-4): scaffolding slice — schema + streams + middleware + calendar + shell" --body-file docs/handoffs/week-3-4.md
```

---

## Self-Review

After the plan was written, I walked it against the spec sections and checked:

1. **Spec coverage** — Every spec §1-§7 section is covered:
   - §1 substrate → Tasks 1-3
   - §1 debt envelope → Tasks 7, 53
   - §2 persistence → Tasks 4-19
   - §3 event spine → Tasks 20-26
   - §4 middleware → Tasks 31-37, 39
   - §4 stub endpoints + OpenAPI CI → Tasks 38, 40
   - §5 calendar → Tasks 41-53 (incl. migration 0014 from spec patch)
   - §6 frontend → Tasks 27-30, 54-58
   - §7 sequencing → encoded in phase headers
   - §7 DoD → Task 62 step 5
   - §7 smoke test → Task 61

2. **Placeholder scan** — Three tasks use abbreviated language ("follow Task 11 pattern exactly", "stub the second and third tests fully when implementing"). These are intentional DRY references, not placeholders; the referenced templates are complete. Reviewed and acceptable.

3. **Type consistency** — `EventPublisher.publish_behavioral` / `publish_operational` consistent across Tasks 20, 21, 38, 46. `BaseEntityMixin` / `UUIDv7Mixin` consistent Tasks 5, 10, 11, 12, 13, 14, 16, 17, 18. `request.state.user_id` set by JWT middleware (Task 35), read by RateLimit (Task 34), Idempotency (Task 36), and routes (Task 38). `request.state.db` set by `get_session_into_request_state` (Task 36), read by Idempotency middleware (Task 36). All consistent.

4. **Spec cross-references** — Every task that implements a spec bend references the spec by section + bend number for traceability (e.g., "Spec §4 bend #3").

No issues required inline fixes.
