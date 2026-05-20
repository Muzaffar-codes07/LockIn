# Slice 0 — Auth + Task Capture Spine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

---

## Execution Status — paused 2026-05-19

Executing via subagent-driven development on branch `feat/slice-0-auth-task-capture-spine`. **Tasks 1–10 are COMPLETE** (implemented, spec-reviewed, code-quality-reviewed, all review issues resolved). **Tasks 11–16 + final review remain.** Resume at Task 11.

| Task | Status | Final commit | Notes |
|------|--------|--------------|-------|
| 1 — `user_uuid` helper | ✅ Done | `563a292` | + v5-version assertion added in review |
| 2 — `Task` model + migration `0003` | ✅ Done | `5289f7a` | migration code verified; live `alembic upgrade` deferred (see env notes) |
| 3 — `TaskCreate`/`TaskRead` schemas | ✅ Done | `04ecc83` | |
| 4 — Redis + `EventPublisher` deps | ✅ Done | `d547d13` | |
| 5 — `TaskService` dual-write | ✅ Done | `3096939` | `create()` `source` param tightened to `TaskSource` in review |
| 6 — `/v1/tasks` routes | ✅ Done | `462afb8` | |
| 7 — Backend test infrastructure | ✅ Done | `26ad735` | 3 review fixes: root `uv.lock` updated, `try/finally` override cleanup, `app`-name-shadow fix |
| 8 — Integration tests for `/v1/tasks` | ✅ Done | `a6215ce` | 6 tests; full backend suite **24 passing** |
| 9 — Shared TypeScript types | ✅ Done | `5a0b1ba` | |
| 10 — React Query provider + layout | ✅ Done | `c1b72c5` | `@tanstack/react-query@^5.100.11` |
| 11 — BFF route `/api/tasks` | ⬜ Not started | — | next |
| 12 — Task data hooks | ⬜ Not started | — | |
| 13 — Command palette + test | ⬜ Not started | — | |
| 14 — Dashboard + landing page | ⬜ Not started | — | |
| 15 — Decision record + handoff | ⬜ Not started | — | |
| 16 — (stretch) task deletion | ⬜ Not started | — | |
| Final code review | ⬜ Not started | — | |

**Environment notes (carry forward — important for Tasks 8/14 and CI):**
- Docker Desktop is running; `docker-postgres-1` + `docker-redis-1` are up.
- **A native PostgreSQL 18 on Windows binds `localhost:5432` and shadows the Docker container's published port.** During Task 8 the `lockin` role and the `lockin` + `lockin_test` databases were bootstrapped on the *native* instance (its `pg_hba.conf` was temporarily set to `trust`, then restored to `scram-sha-256` — not committed). All backend tests therefore run against the native Postgres. Task 14's manual smoke test will also hit the native instance; the dev `lockin` DB there still needs `alembic upgrade head` applied before the smoke test.
- The workspace uses a **single root `uv.lock`**; the stale `apps/api/uv.lock` is ignored by uv in workspace mode.

**Carried-forward review observations (non-blocking, not yet actioned):**
- Migration `0003` (and `0002`) have no DB-side `gen_random_uuid()` default on `id` — ORM supplies `uuid4`; raw-SQL inserts would need a default. Hardening pass, post-Slice-0.
- `TaskService` dual write has no transactional outbox — if the Redis publish fails post-commit the event is lost (documented in the file; outbox is a later slice).
- `created_at`-based ordering has no monotonic tiebreaker — theoretical flake risk if two POSTs share a timestamp (very low; documented in `test_tasks.py`).

---

**Goal:** Build the smallest end-to-end loop that proves the architecture — a signed-in user opens a Cmd+K palette, types a task title, presses Enter, and sees it persist in a list — with the task written to Postgres and a `task.created` event emitted to Redis Streams.

**Architecture:** Next.js 16 web app authenticates with Google via the existing NextAuth v5 setup. A thin Next.js Route Handler (`/api/tasks`) acts as a BFF proxy: it reads the HS256 session-token cookie and forwards it as a `Bearer` token to the FastAPI backend. FastAPI validates the JWT, a `TaskService` dual-writes to Postgres and publishes a `task.created` event to the `events:tasks` Redis Stream. The frontend uses React Query (TanStack Query) for fetching and optimistic-ready mutations.

**Tech Stack:** Next.js 16 / React 19, NextAuth v5, TanStack Query v5, FastAPI, SQLAlchemy 2.0 async + asyncpg, Alembic, Redis Streams, `lockin_events` (generated Pydantic event models), pytest + fakeredis, vitest + Testing Library.

**Data-layer decision:** `CURRENT_SLICE.md` said "server actions or tRPC". Neither reaches the real backend cleanly — the API is FastAPI (Python), so tRPC (TS-only) and Server Actions (Next-runtime-only) cannot call it directly. This plan uses **React Query → Next.js BFF route → FastAPI REST**, consistent with the locked stack (`TanStack Query` in `CLAUDE.md`). Task 14 records this decision.

**Identity note:** There is no `users` table — auth is JWT-strategy (Google `sub` in the token, no DB sessions). Google's `sub` is a numeric string, not a UUID, but the event schema's `user_id` is typed `UUID`. Task 1 introduces `user_uuid()` (a deterministic `uuid5` map) so the DB and the event stream use one consistent UUID per user. Task 14 records this decision.

**Out of scope (do not build):** calendar sync, mood/energy widgets, ML, MCP, scheduling logic, idempotency-key storage, the full Week 3–4 column set (`tenant_id`, `version`, `status`). Keep the `tasks` table minimal; Week 3–4 owns its expansion.

---

## Foundation gate (verify before Task 1)

The code-level foundation is green per `docs/handoffs/week-1-2.md` (tests, typecheck, event round-trip). Before starting, confirm the local stack boots:

- [ ] `pnpm install` completes
- [ ] `docker compose -f infra/docker/docker-compose.yml up -d` brings up Postgres + Redis
- [ ] `cd apps/api && alembic upgrade head` applies migrations `0001`+`0002` cleanly
- [ ] `make api` (or `python -m uvicorn app.main:app --reload` from `apps/api`) serves `http://localhost:8000/health`
- [ ] `pnpm --filter @lockin/web dev` serves `http://localhost:3000`

If any fail, fix or escalate before proceeding — do not scaffold on a broken foundation.

---

## File Structure

**Backend (`apps/api/app/`):**
- `core/identity.py` — *new* — `user_uuid()`: maps OAuth subject → stable UUID.
- `db/models/task.py` — *new* — `Task` ORM model.
- `db/models/__init__.py` — *modify* — register `Task`.
- `alembic/versions/0003_tasks.py` — *new* — `tasks` table migration.
- `schemas/task.py` — *new* — `TaskCreate` / `TaskRead` API contracts.
- `schemas/__init__.py` — *new if absent* — package marker.
- `api/v1/deps.py` — *modify* — add Redis + `EventPublisher` providers.
- `services/task_service.py` — *new* — `TaskService`: create + list, dual-write.
- `api/v1/routes/tasks.py` — *new* — `POST /v1/tasks`, `GET /v1/tasks`.
- `api/v1/router.py` — *modify* — register the tasks router.
- `pyproject.toml` — *modify* — add `fakeredis` dev dependency.

**Backend tests (`apps/api/tests/`):**
- `conftest.py` — *modify* — `db_engine`, `fake_redis`, `db_client` fixtures.
- `unit/test_identity.py` — *new*.
- `integration/test_tasks.py` — *new*.

**Shared (`packages/shared-types/src/`):**
- `index.ts` — *modify* — `TaskCreateRequest`, `TaskResponse`.

**Frontend (`apps/web/`):**
- `package.json` — *modify* — add `@tanstack/react-query` + test deps.
- `src/app/providers.tsx` — *new* — React Query provider.
- `src/app/layout.tsx` — *modify* — wrap children in `Providers`; fix metadata.
- `src/app/page.tsx` — *modify* — landing page sign-in / redirect.
- `src/app/api/tasks/route.ts` — *new* — BFF proxy to FastAPI.
- `src/hooks/use-tasks.ts` — *new* — `useTasks`, `useCreateTask`.
- `src/components/command-palette.tsx` — *new* — Cmd+K modal.
- `src/components/command-palette.test.tsx` — *new*.
- `src/app/dashboard/page.tsx` — *new* — server auth gate.
- `src/app/dashboard/dashboard-client.tsx` — *new* — empty state + list + palette.
- `vitest.config.ts` — *new* — jsdom + React plugin.
- `vitest.setup.ts` — *new* — Testing Library matchers.

**Docs:**
- `docs/decisions/2026-05-18-data-layer.md` — *new*.
- `docs/CURRENT_SLICE.md` — *modify* — point at Week 3–4 Scaffolding.

---

## Task 1: `user_uuid` identity helper

**Files:**
- Create: `apps/api/app/core/identity.py`
- Test: `apps/api/tests/unit/test_identity.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/unit/test_identity.py`:

```python
"""Unit tests for the OAuth-subject → UUID mapping."""

from __future__ import annotations

from uuid import UUID

from app.core.identity import user_uuid


def test_user_uuid_is_stable_for_same_subject() -> None:
    assert user_uuid("117234567890") == user_uuid("117234567890")


def test_user_uuid_differs_per_subject() -> None:
    assert user_uuid("subject-a") != user_uuid("subject-b")


def test_user_uuid_returns_a_uuid() -> None:
    assert isinstance(user_uuid("117234567890"), UUID)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && pytest tests/unit/test_identity.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.core.identity'`

- [ ] **Step 3: Write minimal implementation**

Create `apps/api/app/core/identity.py`:

```python
"""Map an external OAuth subject to a stable internal UUID.

Auth is JWT-strategy: there is no `users` table, and the identity we receive
is Google's `sub` claim — a numeric string, not a UUID. The event schema and
every per-user table key on `UUID`. `user_uuid` derives a deterministic v5
UUID from the subject so Postgres rows and the `task.created` event stream
agree on one identifier per user.
"""

from __future__ import annotations

from uuid import UUID, uuid5

# Fixed namespace for user-identity derivation. Generated once for LockIn.
# NEVER change this value — changing it re-keys every existing user.
_USER_NAMESPACE = UUID("9f2a7c4e-0b1d-4e6a-8c3f-1a2b3c4d5e6f")


def user_uuid(subject: str) -> UUID:
    """Return the stable internal UUID for an OAuth subject (e.g. Google `sub`)."""
    return uuid5(_USER_NAMESPACE, subject)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/api && pytest tests/unit/test_identity.py -v`
Expected: PASS — 3 passed

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/core/identity.py apps/api/tests/unit/test_identity.py
git commit -m "feat(api): add user_uuid identity helper for OAuth subject mapping"
```

---

## Task 2: `Task` ORM model + Alembic migration

**Files:**
- Create: `apps/api/app/db/models/task.py`
- Modify: `apps/api/app/db/models/__init__.py`
- Create: `apps/api/alembic/versions/0003_tasks.py`

- [ ] **Step 1: Create the ORM model**

Create `apps/api/app/db/models/task.py`:

```python
"""Task rows — a user-captured unit of work.

Slice 0 keeps this table intentionally minimal (YAGNI). Week 3–4 Scaffolding
owns the expansion (`tenant_id`, `version`, `status`, indexes). Do not add
those columns here.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False, server_default="keyboard")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
```

- [ ] **Step 2: Register the model so `Base.metadata` and Alembic see it**

Replace the contents of `apps/api/app/db/models/__init__.py`:

```python
"""SQLAlchemy ORM models.

Importing this package side-effects: every model module here is loaded so
``Base.metadata`` sees the tables. Alembic's ``env.py`` imports this package
for the same reason — see the note in ``alembic/env.py``.
"""

from app.db.models.credential import WebauthnCredential  # noqa: F401
from app.db.models.task import Task  # noqa: F401

__all__ = ["Task", "WebauthnCredential"]
```

- [ ] **Step 3: Create the Alembic migration**

Create `apps/api/alembic/versions/0003_tasks.py`:

```python
"""tasks

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("source", sa.String(16), nullable=False, server_default="keyboard"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("tasks")
```

- [ ] **Step 4: Verify the migration runs both directions**

Run (with Postgres up from the foundation gate):

```bash
cd apps/api
alembic upgrade head      # expect: ... Running upgrade 0002 -> 0003, tasks
alembic downgrade -1      # expect: ... Running downgrade 0003 -> 0002
alembic upgrade head      # expect: re-applies 0003 cleanly
```

Expected: each command exits 0; `tasks` table exists after the final `upgrade`.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/db/models/task.py apps/api/app/db/models/__init__.py apps/api/alembic/versions/0003_tasks.py
git commit -m "feat(api): add tasks table model and migration 0003"
```

---

## Task 3: API request/response schemas

**Files:**
- Create: `apps/api/app/schemas/__init__.py`
- Create: `apps/api/app/schemas/task.py`

- [ ] **Step 1: Create the schemas package marker**

Create `apps/api/app/schemas/__init__.py`:

```python
"""API request/response Pydantic models. Not ORM models, not event models."""
```

- [ ] **Step 2: Create the task schemas**

Create `apps/api/app/schemas/task.py`:

```python
"""Request/response contracts for the /v1/tasks endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

TaskSource = Literal["keyboard", "click", "voice", "mcp"]


class TaskCreate(BaseModel):
    """Body of `POST /v1/tasks`."""

    title: str = Field(min_length=1, max_length=500)
    source: TaskSource = "keyboard"


class TaskRead(BaseModel):
    """A task as returned by the API. Built from the ORM row."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    source: str
    created_at: datetime
```

- [ ] **Step 3: Commit**

```bash
git add apps/api/app/schemas/__init__.py apps/api/app/schemas/task.py
git commit -m "feat(api): add TaskCreate/TaskRead API schemas"
```

---

## Task 4: Redis + EventPublisher dependency providers

**Files:**
- Modify: `apps/api/app/api/v1/deps.py`

- [ ] **Step 1: Add the Redis and publisher providers**

Replace the contents of `apps/api/app/api/v1/deps.py`:

```python
"""FastAPI dependency providers: DB sessions, Redis, event publisher."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.events.publisher import EventPublisher, get_redis


async def _db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(_db_session)]


async def _redis() -> AsyncIterator[Redis]:
    redis = get_redis()
    try:
        yield redis
    finally:
        await redis.aclose()


RedisDep = Annotated[Redis, Depends(_redis)]


async def _event_publisher(redis: RedisDep) -> EventPublisher:
    return EventPublisher(redis)


EventPublisherDep = Annotated[EventPublisher, Depends(_event_publisher)]
```

- [ ] **Step 2: Verify the API still imports cleanly**

Run: `cd apps/api && python -c "from app.main import app; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add apps/api/app/api/v1/deps.py
git commit -m "feat(api): add Redis and EventPublisher FastAPI dependencies"
```

---

## Task 5: `TaskService` — dual-write to Postgres + Redis

**Files:**
- Create: `apps/api/app/services/task_service.py`

Tested via the integration tests in Task 8 (it needs a live DB + Redis, which the test fixtures provide). No standalone unit test — a mock-DB unit test here would prove nothing.

- [ ] **Step 1: Create the service**

Create `apps/api/app/services/task_service.py`:

```python
"""Task creation and listing.

`create` performs a dual write: the row is committed to Postgres, then a
`task.created` event is published to the `events:tasks` Redis Stream. This is
a deliberate Slice-0 simplification — the transactional outbox pattern lands
in a later slice. The publish happens only after a successful commit.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from lockin_events import STREAM_TASKS, TaskCreated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.task import Task
from app.events.publisher import EventPublisher


class TaskService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        publisher: EventPublisher,
        *,
        user_id: UUID,
        title: str,
        source: str,
    ) -> Task:
        task = Task(id=uuid4(), user_id=user_id, title=title, source=source)
        self._session.add(task)
        await self._session.commit()
        await self._session.refresh(task)

        event = TaskCreated.model_validate(
            {
                "event_id": str(uuid4()),
                "event_type": "task.created",
                "event_version": 1,
                "user_id": str(user_id),
                "tenant_id": None,
                "occurred_at": task.created_at.isoformat(),
                "client_idempotency_key": None,
                "source": "web",
                "payload": {
                    "task_id": str(task.id),
                    "title": task.title,
                    "source": task.source,
                },
            }
        )
        await publisher.publish(STREAM_TASKS, event)
        return task

    async def list_for_user(self, user_id: UUID) -> list[Task]:
        result = await self._session.execute(
            select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())
```

- [ ] **Step 2: Verify it imports**

Run: `cd apps/api && python -c "from app.services.task_service import TaskService; print('ok')"`
Expected: `ok` — confirms `lockin_events` exports `TaskCreated` and `STREAM_TASKS`.

- [ ] **Step 3: Commit**

```bash
git add apps/api/app/services/task_service.py
git commit -m "feat(api): add TaskService with Postgres + Redis dual write"
```

---

## Task 6: `/v1/tasks` routes

**Files:**
- Create: `apps/api/app/api/v1/routes/tasks.py`
- Modify: `apps/api/app/api/v1/router.py`

- [ ] **Step 1: Create the routes**

Create `apps/api/app/api/v1/routes/tasks.py`:

```python
"""`/v1/tasks` — create and list a user's captured tasks."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.v1.deps import DbSession, EventPublisherDep
from app.core.auth import CurrentUserDep
from app.core.identity import user_uuid
from app.schemas.task import TaskCreate, TaskRead
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    user: CurrentUserDep,
    session: DbSession,
    publisher: EventPublisherDep,
) -> TaskRead:
    service = TaskService(session)
    task = await service.create(
        publisher,
        user_id=user_uuid(user.user_id),
        title=body.title,
        source=body.source,
    )
    return TaskRead.model_validate(task)


@router.get("", response_model=list[TaskRead])
async def list_tasks(user: CurrentUserDep, session: DbSession) -> list[TaskRead]:
    service = TaskService(session)
    tasks = await service.list_for_user(user_uuid(user.user_id))
    return [TaskRead.model_validate(task) for task in tasks]
```

- [ ] **Step 2: Register the router**

Replace the contents of `apps/api/app/api/v1/router.py`:

```python
"""Aggregates all v1 routers under the /v1 prefix."""

from fastapi import APIRouter

from app.api.v1.routes import debug, health, me, tasks, webauthn

api_router = APIRouter(prefix="/v1")
api_router.include_router(health.router)
api_router.include_router(me.router)
api_router.include_router(tasks.router)
api_router.include_router(webauthn.router)
api_router.include_router(debug.router)
```

- [ ] **Step 3: Verify the app boots and the routes register**

Run: `cd apps/api && python -c "from app.main import app; print(sorted(r.path for r in app.routes if 'tasks' in r.path))"`
Expected: `['/v1/tasks']`

- [ ] **Step 4: Commit**

```bash
git add apps/api/app/api/v1/routes/tasks.py apps/api/app/api/v1/router.py
git commit -m "feat(api): add POST and GET /v1/tasks endpoints"
```

---

## Task 7: Backend test infrastructure

**Files:**
- Modify: `apps/api/pyproject.toml`
- Modify: `apps/api/tests/conftest.py`

- [ ] **Step 1: Add `fakeredis` to dev dependencies**

In `apps/api/pyproject.toml`, inside `[project.optional-dependencies]` → `dev`, add `fakeredis` after the `httpx` line:

```toml
    "httpx>=0.28",            # also for TestClient
    "fakeredis>=2.26",        # in-memory Redis (incl. Streams) for tests
```

- [ ] **Step 2: Install the new dependency**

Run: `cd apps/api && uv sync --extra dev`
Expected: resolves and installs `fakeredis`.

- [ ] **Step 3: Create the `lockin_test` database (one-time)**

Run (Postgres up from the foundation gate):

```bash
docker compose -f infra/docker/docker-compose.yml exec -T postgres createdb -U lockin lockin_test
```

Expected: exits 0 (or "already exists" — harmless; the fixture drops/recreates tables each test).

- [ ] **Step 4: Extend conftest with DB + Redis fixtures**

Replace the contents of `apps/api/tests/conftest.py`:

```python
"""Shared pytest fixtures."""

from collections.abc import AsyncIterator

import fakeredis.aioredis
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.db.models  # noqa: F401 -- registers all models on Base.metadata
from app.api.v1.deps import _db_session, _redis
from app.core.config import settings
from app.db.base import Base
from app.main import app


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    # raise_app_exceptions=False makes uncaught exceptions surface as 500
    # responses, matching production ASGI servers.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _test_db_url() -> str:
    """Derive the test DB URL from DATABASE_URL by swapping the database name."""
    base, _, _name = settings.DATABASE_URL.rpartition("/")
    return f"{base}/lockin_test"


@pytest_asyncio.fixture
async def db_engine() -> AsyncIterator[object]:
    engine = create_async_engine(_test_db_url(), future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def fake_redis() -> AsyncIterator[fakeredis.aioredis.FakeRedis]:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield redis
    await redis.aclose()


@pytest_asyncio.fixture
async def db_client(
    db_engine: object,
    fake_redis: fakeredis.aioredis.FakeRedis,
) -> AsyncIterator[AsyncClient]:
    """An HTTP client whose API uses the test DB and an in-memory Redis."""
    maker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_db() -> AsyncIterator[AsyncSession]:
        async with maker() as session:
            yield session

    async def _override_redis() -> AsyncIterator[fakeredis.aioredis.FakeRedis]:
        yield fake_redis

    app.dependency_overrides[_db_session] = _override_db
    app.dependency_overrides[_redis] = _override_redis

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
```

- [ ] **Step 5: Verify the existing suite still passes**

Run: `cd apps/api && pytest tests/integration/test_health.py tests/integration/test_webauthn.py -v`
Expected: all pass — the untouched `client` fixture still works.

- [ ] **Step 6: Commit**

```bash
git add apps/api/pyproject.toml apps/api/uv.lock apps/api/tests/conftest.py
git commit -m "test(api): add DB and fakeredis fixtures for task endpoint tests"
```

---

## Task 8: Integration tests for `/v1/tasks`

**Files:**
- Create: `apps/api/tests/integration/test_tasks.py`

- [ ] **Step 1: Write the failing tests**

Create `apps/api/tests/integration/test_tasks.py`:

```python
"""Integration tests for the /v1/tasks endpoints.

These exercise the full slice spine: JWT auth -> DB write -> event publish.
The DB is the `lockin_test` database; Redis is an in-memory fake.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import fakeredis.aioredis
from httpx import AsyncClient
from jose import jwt  # type: ignore[import-untyped]
from lockin_events import STREAM_TASKS

from app.core.config import settings


def _bearer(subject: str = "google-sub-117234567890") -> str:
    token = jwt.encode(
        {
            "user_id": subject,
            "email": "muzaffar@example.com",
            "providers": ["google"],
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALG,
    )
    return f"Bearer {token}"


async def test_create_task_requires_auth(db_client: AsyncClient) -> None:
    res = await db_client.post("/v1/tasks", json={"title": "no auth"})
    assert res.status_code == 401


async def test_create_task_rejects_empty_title(db_client: AsyncClient) -> None:
    res = await db_client.post(
        "/v1/tasks",
        headers={"Authorization": _bearer()},
        json={"title": ""},
    )
    assert res.status_code == 422


async def test_create_task_returns_201_with_the_task(db_client: AsyncClient) -> None:
    res = await db_client.post(
        "/v1/tasks",
        headers={"Authorization": _bearer()},
        json={"title": "Finish the spec doc"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "Finish the spec doc"
    assert body["source"] == "keyboard"
    assert "id" in body and "created_at" in body


async def test_create_task_emits_task_created_event(
    db_client: AsyncClient,
    fake_redis: fakeredis.aioredis.FakeRedis,
) -> None:
    await db_client.post(
        "/v1/tasks",
        headers={"Authorization": _bearer()},
        json={"title": "Emit an event"},
    )
    entries = await fake_redis.xrange(STREAM_TASKS)
    assert len(entries) == 1
    _entry_id, fields = entries[0]
    event = json.loads(fields["data"])
    assert event["event_type"] == "task.created"
    assert event["event_version"] == 1
    assert event["payload"]["title"] == "Emit an event"


async def test_list_tasks_returns_user_tasks_newest_first(db_client: AsyncClient) -> None:
    headers = {"Authorization": _bearer()}
    await db_client.post("/v1/tasks", headers=headers, json={"title": "first"})
    await db_client.post("/v1/tasks", headers=headers, json={"title": "second"})

    res = await db_client.get("/v1/tasks", headers=headers)
    assert res.status_code == 200
    titles = [t["title"] for t in res.json()]
    assert titles == ["second", "first"]


async def test_list_tasks_isolates_by_user(db_client: AsyncClient) -> None:
    await db_client.post(
        "/v1/tasks",
        headers={"Authorization": _bearer("user-a")},
        json={"title": "owned by A"},
    )
    res = await db_client.get(
        "/v1/tasks",
        headers={"Authorization": _bearer("user-b")},
    )
    assert res.status_code == 200
    assert res.json() == []
```

- [ ] **Step 2: Run the tests**

Run: `cd apps/api && pytest tests/integration/test_tasks.py -v`
Expected: 6 passed.

- [ ] **Step 3: Commit**

```bash
git add apps/api/tests/integration/test_tasks.py
git commit -m "test(api): cover /v1/tasks auth, persistence, and event emission"
```

---

## Task 9: Shared TypeScript types

**Files:**
- Modify: `packages/shared-types/src/index.ts`

- [ ] **Step 1: Define the task contracts**

Replace the contents of `packages/shared-types/src/index.ts`:

```typescript
// Shared API request/response types. Must stay in sync with
// apps/api/app/schemas/task.py.

export type TaskSource = "keyboard" | "click" | "voice" | "mcp";

export interface TaskCreateRequest {
  title: string;
  source?: TaskSource;
}

export interface TaskResponse {
  id: string;
  title: string;
  source: string;
  created_at: string;
}
```

- [ ] **Step 2: Verify the workspace still typechecks**

Run: `pnpm --filter @lockin/shared-types typecheck` (or `pnpm typecheck` if the package has no standalone script)
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add packages/shared-types/src/index.ts
git commit -m "feat(shared-types): add TaskCreateRequest and TaskResponse"
```

---

## Task 10: React Query provider + layout

**Files:**
- Modify: `apps/web/package.json`
- Create: `apps/web/src/app/providers.tsx`
- Modify: `apps/web/src/app/layout.tsx`

- [ ] **Step 1: Install React Query**

Run: `pnpm --filter @lockin/web add @tanstack/react-query`
Expected: `@tanstack/react-query` added to `apps/web/package.json` dependencies.

- [ ] **Step 2: Create the Providers wrapper**

Create `apps/web/src/app/providers.tsx`:

```tsx
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
      }),
  );
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
```

- [ ] **Step 3: Wrap the app in Providers and fix metadata**

Replace the contents of `apps/web/src/app/layout.tsx`:

```tsx
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LockIn",
  description: "Mood-and-energy-aware productivity agent.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

- [ ] **Step 4: Verify the web app builds**

Run: `pnpm --filter @lockin/web typecheck`
Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add apps/web/package.json apps/web/src/app/providers.tsx apps/web/src/app/layout.tsx pnpm-lock.yaml
git commit -m "feat(web): add React Query provider and fix root metadata"
```

---

## Task 11: BFF route handler — `/api/tasks`

**Files:**
- Create: `apps/web/src/app/api/tasks/route.ts`

- [ ] **Step 1: Create the proxy route**

Create `apps/web/src/app/api/tasks/route.ts`:

```ts
// BFF proxy: the browser calls this same-origin route; it reads the HttpOnly
// NextAuth session-token cookie and forwards it as a Bearer token to the
// FastAPI backend. This keeps the backend URL and the token off the client
// and avoids CORS entirely.

import { type NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

// Must match the cookie name configured in apps/web/src/auth.ts.
const SESSION_COOKIE =
  process.env.NODE_ENV === "production"
    ? "__Secure-lockin.session-token"
    : "lockin.session-token";

function bearer(req: NextRequest): string | null {
  const token = req.cookies.get(SESSION_COOKIE)?.value;
  return token ? `Bearer ${token}` : null;
}

export async function GET(req: NextRequest) {
  const auth = bearer(req);
  if (!auth) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const res = await fetch(`${API_BASE_URL}/v1/tasks`, {
    headers: { Authorization: auth },
    cache: "no-store",
  });
  return NextResponse.json(await res.json(), { status: res.status });
}

export async function POST(req: NextRequest) {
  const auth = bearer(req);
  if (!auth) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const body = await req.text();
  const res = await fetch(`${API_BASE_URL}/v1/tasks`, {
    method: "POST",
    headers: { Authorization: auth, "Content-Type": "application/json" },
    body,
  });
  return NextResponse.json(await res.json(), { status: res.status });
}
```

- [ ] **Step 2: Verify it typechecks**

Run: `pnpm --filter @lockin/web typecheck`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/app/api/tasks/route.ts
git commit -m "feat(web): add /api/tasks BFF proxy to the FastAPI backend"
```

---

## Task 12: Task data hooks

**Files:**
- Create: `apps/web/src/hooks/use-tasks.ts`

- [ ] **Step 1: Create the hooks**

Create `apps/web/src/hooks/use-tasks.ts`:

```ts
"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { TaskCreateRequest, TaskResponse } from "@lockin/shared-types";

const TASKS_KEY = ["tasks"] as const;

async function fetchTasks(): Promise<TaskResponse[]> {
  const res = await fetch("/api/tasks", { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Failed to load tasks");
  }
  return res.json();
}

async function createTask(input: TaskCreateRequest): Promise<TaskResponse> {
  const res = await fetch("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    throw new Error("Failed to create task");
  }
  return res.json();
}

export function useTasks() {
  return useQuery({ queryKey: TASKS_KEY, queryFn: fetchTasks });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createTask,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TASKS_KEY }),
  });
}
```

- [ ] **Step 2: Verify it typechecks**

Run: `pnpm --filter @lockin/web typecheck`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/hooks/use-tasks.ts
git commit -m "feat(web): add useTasks and useCreateTask query hooks"
```

---

## Task 13: Command palette component + test

**Files:**
- Create: `apps/web/src/components/command-palette.tsx`
- Create: `apps/web/vitest.config.ts`
- Create: `apps/web/vitest.setup.ts`
- Modify: `apps/web/package.json`
- Create: `apps/web/src/components/command-palette.test.tsx`

- [ ] **Step 1: Create the component**

Create `apps/web/src/components/command-palette.tsx`:

```tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { Button, Input, Stack, Text } from "@lockin/ui";

export interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (title: string) => void;
}

export function CommandPalette({ open, onOpenChange, onSubmit }: CommandPaletteProps) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        onOpenChange(!open);
      }
      if (e.key === "Escape") {
        onOpenChange(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onOpenChange]);

  useEffect(() => {
    if (open) {
      inputRef.current?.focus();
    }
  }, [open]);

  if (!open) {
    return null;
  }

  function submit() {
    const title = value.trim();
    if (!title) {
      return;
    }
    onSubmit(title);
    setValue("");
    onOpenChange(false);
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Add a task"
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 pt-32"
      onClick={() => onOpenChange(false)}
    >
      <div
        className="w-full max-w-lg rounded-lg bg-surface p-4 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <Stack gap={3}>
          <Text size="sm" tone="muted">
            Add a task
          </Text>
          <Input
            ref={inputRef}
            value={value}
            placeholder="What needs doing?"
            aria-label="Task title"
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                submit();
              }
            }}
          />
          <Button variant="primary" onClick={submit}>
            Add task
          </Button>
        </Stack>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add web test dependencies**

Run: `pnpm --filter @lockin/web add -D @testing-library/react @testing-library/jest-dom jsdom @vitejs/plugin-react`
Expected: the four packages added to `apps/web` devDependencies.

- [ ] **Step 3: Create the vitest config and setup**

Create `apps/web/vitest.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": resolve(__dirname, "./src") },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    passWithNoTests: true,
  },
});
```

Create `apps/web/vitest.setup.ts`:

```ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 4: Write the component test**

Create `apps/web/src/components/command-palette.test.tsx`:

```tsx
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { CommandPalette } from "./command-palette";

describe("CommandPalette", () => {
  it("renders nothing when closed", () => {
    const { container } = render(
      <CommandPalette open={false} onOpenChange={() => {}} onSubmit={() => {}} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("submits the trimmed title and closes on Enter", () => {
    const onSubmit = vi.fn();
    const onOpenChange = vi.fn();
    render(<CommandPalette open onOpenChange={onOpenChange} onSubmit={onSubmit} />);

    const input = screen.getByPlaceholderText("What needs doing?");
    fireEvent.change(input, { target: { value: "  Write the spec  " } });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(onSubmit).toHaveBeenCalledWith("Write the spec");
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("ignores a blank title", () => {
    const onSubmit = vi.fn();
    render(<CommandPalette open onOpenChange={() => {}} onSubmit={onSubmit} />);

    const input = screen.getByPlaceholderText("What needs doing?");
    fireEvent.change(input, { target: { value: "   " } });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(onSubmit).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 5: Run the test**

Run: `pnpm --filter @lockin/web test`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/components/command-palette.tsx apps/web/src/components/command-palette.test.tsx apps/web/vitest.config.ts apps/web/vitest.setup.ts apps/web/package.json pnpm-lock.yaml
git commit -m "feat(web): add Cmd+K command palette with tests"
```

---

## Task 14: Dashboard route + landing page

**Files:**
- Create: `apps/web/src/app/dashboard/page.tsx`
- Create: `apps/web/src/app/dashboard/dashboard-client.tsx`
- Modify: `apps/web/src/app/page.tsx`

- [ ] **Step 1: Create the dashboard server gate**

Create `apps/web/src/app/dashboard/page.tsx`:

```tsx
import { redirect } from "next/navigation";
import { auth } from "@/auth";
import { DashboardClient } from "./dashboard-client";

export default async function DashboardPage() {
  const session = await auth();
  if (!session) {
    redirect("/");
  }
  return <DashboardClient />;
}
```

- [ ] **Step 2: Create the dashboard client**

Create `apps/web/src/app/dashboard/dashboard-client.tsx`:

```tsx
"use client";

import { useState } from "react";
import { Button, Card, Stack, Text } from "@lockin/ui";
import { CommandPalette } from "@/components/command-palette";
import { useCreateTask, useTasks } from "@/hooks/use-tasks";

export function DashboardClient() {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const { data: tasks = [], isPending } = useTasks();
  const createTask = useCreateTask();

  return (
    <main className="mx-auto w-full max-w-2xl p-6">
      <Stack gap={5}>
        <Text as="h1" size="3xl" weight="bold">
          Today
        </Text>

        <Button variant="secondary" onClick={() => setPaletteOpen(true)}>
          Add a task — ⌘K
        </Button>

        {isPending ? (
          <Text tone="muted">Loading…</Text>
        ) : tasks.length === 0 ? (
          <Card>
            <Stack gap={2} align="center">
              <Text weight="bold">No tasks yet</Text>
              <Text tone="muted">Press ⌘K to add your first task.</Text>
            </Stack>
          </Card>
        ) : (
          <Stack gap={2}>
            {tasks.map((task) => (
              <Card key={task.id}>
                <Text>{task.title}</Text>
              </Card>
            ))}
          </Stack>
        )}
      </Stack>

      <CommandPalette
        open={paletteOpen}
        onOpenChange={setPaletteOpen}
        onSubmit={(title) => createTask.mutate({ title, source: "keyboard" })}
      />
    </main>
  );
}
```

- [ ] **Step 3: Replace the landing page with sign-in / redirect**

Replace the contents of `apps/web/src/app/page.tsx`:

```tsx
import { redirect } from "next/navigation";
import { auth, signIn } from "@/auth";
import { Button, Stack, Text } from "@lockin/ui";

export default async function Home() {
  const session = await auth();
  if (session) {
    redirect("/dashboard");
  }

  return (
    <main className="min-h-dvh grid place-items-center">
      <Stack gap={4} align="center">
        <Text as="h1" size="3xl" weight="bold">
          LockIn
        </Text>
        <Text tone="muted">Mood-aware productivity. Sign in to start.</Text>
        <form
          action={async () => {
            "use server";
            await signIn("google", { redirectTo: "/dashboard" });
          }}
        >
          <Button type="submit" variant="primary">
            Sign in with Google
          </Button>
        </form>
      </Stack>
    </main>
  );
}
```

- [ ] **Step 4: Verify the web app typechecks and builds**

Run: `pnpm --filter @lockin/web typecheck`
Expected: no errors.

- [ ] **Step 5: Manual smoke test of the full loop**

With Postgres + Redis up, `make api` running, and `pnpm --filter @lockin/web dev` running:

1. Visit `http://localhost:3000` → see "Sign in with Google".
2. Sign in → land on `/dashboard` with the "No tasks yet" empty state.
3. Press ⌘K (or Ctrl+K) → palette opens. Type `Finish spec doc`, press Enter.
4. Task appears in the list. Refresh the page → task still there.
5. `docker compose -f infra/docker/docker-compose.yml exec -T postgres psql -U lockin -d lockin -c "SELECT id, user_id, title FROM tasks;"` → shows the row.
6. `docker compose -f infra/docker/docker-compose.yml exec -T redis redis-cli XRANGE events:tasks - +` → shows a `task.created` event.

Expected: all six steps succeed.

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/app/dashboard/page.tsx apps/web/src/app/dashboard/dashboard-client.tsx apps/web/src/app/page.tsx
git commit -m "feat(web): add dashboard with task capture loop and sign-in landing"
```

---

## Task 15: Decision record + slice handoff

**Files:**
- Create: `docs/decisions/2026-05-18-data-layer.md`
- Modify: `docs/CURRENT_SLICE.md`

- [ ] **Step 1: Write the decision record**

Create `docs/decisions/2026-05-18-data-layer.md`:

```markdown
# Decision: Frontend data layer + user-identity mapping (Slice 0)

**Date:** 2026-05-18
**Status:** Accepted

## Context

`CURRENT_SLICE.md` instructed "use server actions or tRPC". The real backend
is FastAPI (Python); tRPC is TypeScript-only and Server Actions run only in
the Next.js runtime — neither calls FastAPI directly. Separately, auth is
JWT-strategy with no `users` table: identity is Google's `sub` (a numeric
string), but the event schema types `user_id` as `UUID`.

## Decision

1. **Data layer:** React Query (TanStack Query, already locked in `CLAUDE.md`)
   on the client, calling a thin Next.js BFF route handler (`/api/tasks`) that
   forwards the HttpOnly session-token cookie as a Bearer token to FastAPI.
2. **Identity:** `app/core/identity.py:user_uuid()` maps an OAuth subject to a
   deterministic `uuid5` UUID, used as the key for every per-user row and event.

## Consequences

- No CORS surface — the browser only talks to same-origin Next.js routes.
- React Query's mutation primitives are ready for the Week 5 optimistic mood UI.
- The `_USER_NAMESPACE` constant in `identity.py` must never change — doing so
  re-keys every user. A real `users` table (P2 team mode) can adopt the same
  derived UUID as its primary key with no data migration.
```

- [ ] **Step 2: Update CURRENT_SLICE.md**

Replace the contents of `docs/CURRENT_SLICE.md`:

```markdown
# Current Slice — Week 3–4 Scaffolding

> **✅ Slice 0 (Auth + Task Capture Spine) complete (2026-05-18):** Signed-in
> users capture tasks via a Cmd+K palette; tasks persist to Postgres and emit
> `task.created` to the `events:tasks` Redis Stream. Plan + outcome:
> [`docs/superpowers/plans/2026-05-18-slice-0-auth-task-capture-spine.md`](superpowers/plans/2026-05-18-slice-0-auth-task-capture-spine.md).

**Status:** Ready to start
**Est. duration:** 10 working days

## The Goal

Scaffolding — grow the skeleton's organs. See the full handoff for the six
deliverables: Postgres schemas + Alembic migrations, TimescaleDB hypertables,
Redis Streams consumer groups, the API gateway middleware stack, Google
Calendar read-only sync, and the frontend shell. Zero user-facing features.

## What's Next

After Week 3–4 ships, Week 5–6 builds the capture loop (voice + text input,
mood/energy widget, notification permissions, real event instrumentation).

---
*Update this file when the slice ships. Archive previous slices in `docs/slices/`.*
```

- [ ] **Step 3: Run the full backend + frontend test suites**

Run:

```bash
cd apps/api && pytest -q
cd ../.. && pnpm --filter @lockin/web test && pnpm --filter @lockin/web typecheck
```

Expected: all green.

- [ ] **Step 4: Commit**

```bash
git add docs/decisions/2026-05-18-data-layer.md docs/CURRENT_SLICE.md
git commit -m "docs: record Slice 0 data-layer decision and advance CURRENT_SLICE"
```

---

## Task 16 (Stretch — only if ahead of schedule): Delete a task

Build only if Tasks 1–15 are done and verified. This exercises idempotency thinking in the simplest context.

**Files:**
- Modify: `apps/api/app/services/task_service.py`
- Modify: `apps/api/app/api/v1/routes/tasks.py`
- Modify: `apps/api/tests/integration/test_tasks.py`
- Modify: `apps/web/src/hooks/use-tasks.ts`
- Modify: `apps/web/src/app/dashboard/dashboard-client.tsx`

- [ ] **Step 1: Add `delete` to `TaskService`**

Add this method to `TaskService` in `apps/api/app/services/task_service.py` (after `list_for_user`):

```python
    async def delete(self, *, user_id: UUID, task_id: UUID) -> bool:
        """Delete a task. Returns False if it does not exist for this user.

        Idempotent: deleting an already-absent task is not an error — the
        caller's desired end state (task gone) is satisfied either way.
        """
        result = await self._session.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        )
        task = result.scalar_one_or_none()
        if task is None:
            return False
        await self._session.delete(task)
        await self._session.commit()
        return True
```

- [ ] **Step 2: Add the DELETE route**

Add to `apps/api/app/api/v1/routes/tasks.py` (after `list_tasks`); add `UUID` to the imports and `Response` to the FastAPI import:

```python
from uuid import UUID

from fastapi import APIRouter, Response, status
```

```python
@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    user: CurrentUserDep,
    session: DbSession,
) -> Response:
    service = TaskService(session)
    # Idempotent: 204 whether or not the row existed.
    await service.delete(user_id=user_uuid(user.user_id), task_id=task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 3: Add the integration test**

Add to `apps/api/tests/integration/test_tasks.py`:

```python
async def test_delete_task_is_idempotent(db_client: AsyncClient) -> None:
    headers = {"Authorization": _bearer()}
    created = await db_client.post("/v1/tasks", headers=headers, json={"title": "doomed"})
    task_id = created.json()["id"]

    first = await db_client.delete(f"/v1/tasks/{task_id}", headers=headers)
    assert first.status_code == 204

    # Deleting again is still 204 — desired end state already holds.
    second = await db_client.delete(f"/v1/tasks/{task_id}", headers=headers)
    assert second.status_code == 204

    remaining = await db_client.get("/v1/tasks", headers=headers)
    assert remaining.json() == []
```

- [ ] **Step 4: Run the backend tests**

Run: `cd apps/api && pytest tests/integration/test_tasks.py -v`
Expected: 7 passed.

- [ ] **Step 5: Add the `useDeleteTask` hook**

Add to `apps/web/src/hooks/use-tasks.ts` (after `createTask`, and export the hook):

```ts
async function deleteTask(id: string): Promise<void> {
  const res = await fetch(`/api/tasks?id=${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error("Failed to delete task");
  }
}

export function useDeleteTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteTask,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TASKS_KEY }),
  });
}
```

- [ ] **Step 6: Add a DELETE handler to the BFF route**

Add to `apps/web/src/app/api/tasks/route.ts`:

```ts
export async function DELETE(req: NextRequest) {
  const auth = bearer(req);
  if (!auth) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const id = req.nextUrl.searchParams.get("id");
  if (!id) {
    return NextResponse.json({ error: "missing id" }, { status: 400 });
  }
  const res = await fetch(`${API_BASE_URL}/v1/tasks/${id}`, {
    method: "DELETE",
    headers: { Authorization: auth },
  });
  return new NextResponse(null, { status: res.status });
}
```

- [ ] **Step 7: Add a delete button to the task list**

In `apps/web/src/app/dashboard/dashboard-client.tsx`, import and use `useDeleteTask`, and replace the task `Card` block:

```tsx
import { useCreateTask, useDeleteTask, useTasks } from "@/hooks/use-tasks";
```

```tsx
            {tasks.map((task) => (
              <Card key={task.id}>
                <div className="flex items-center justify-between gap-3">
                  <Text>{task.title}</Text>
                  <Button
                    variant="ghost"
                    size="sm"
                    aria-label={`Delete ${task.title}`}
                    onClick={() => deleteTask.mutate(task.id)}
                  >
                    Delete
                  </Button>
                </div>
              </Card>
            ))}
```

Add `const deleteTask = useDeleteTask();` next to `const createTask = useCreateTask();`.

- [ ] **Step 8: Verify and commit**

Run: `cd apps/api && pytest -q && cd ../.. && pnpm --filter @lockin/web typecheck`
Expected: all green.

```bash
git add apps/api/app/services/task_service.py apps/api/app/api/v1/routes/tasks.py apps/api/tests/integration/test_tasks.py apps/web/src/hooks/use-tasks.ts apps/web/src/app/api/tasks/route.ts apps/web/src/app/dashboard/dashboard-client.tsx
git commit -m "feat: add idempotent task deletion (stretch)"
```

---

## Definition of Done

- [ ] `alembic upgrade head` creates the `tasks` table; `downgrade` removes it.
- [ ] `pytest apps/api` is fully green, including the six `/v1/tasks` integration tests.
- [ ] `pnpm --filter @lockin/web test` and `typecheck` are green.
- [ ] Manual loop (Task 14 Step 5) verified: sign in → ⌘K → type → Enter → task in list → survives refresh → row in Postgres → `task.created` in `events:tasks`.
- [ ] `docs/CURRENT_SLICE.md` points at Week 3–4 Scaffolding.
- [ ] Data-layer + identity decision recorded in `docs/decisions/`.
