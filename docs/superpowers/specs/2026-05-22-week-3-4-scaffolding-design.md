# Week 3-4 Scaffolding — Design Spec

> **Date:** 2026-05-22
> **Slice:** Week 3-4 (Scaffolding)
> **Status:** Approved through 7 rounds of section-by-section bends (§1-§7); ready for `writing-plans`.
> **Branch:** `feat/week-3-4-scaffolding`
> **Driving handoff:** Week 3-4 thread (chat, 2026-05-22). Non-negotiables captured in [Scope](#scope) below.
> **Implementation plan:** TBD — `superpowers:writing-plans` invoked after Md approves this spec.

---

## Scope

10 working days. Six deliverables. **Zero user-facing features.** Single branch `feat/week-3-4-scaffolding`, one PR, six logical commits, squash-merge.

Mandate verbatim from the handoff: *"By Day 10, an authenticated user can hit a working API gateway, their request flows through middleware that emits events to Redis Streams, lands in Postgres + TimescaleDB tables that already know their final shape, and their Google Calendar reads into the system on a polling loop. The frontend shell renders the empty-state version of every main view."*

If anything in this spec implies user-facing logic (scheduling algorithm, mood widget interaction, LLM calls, explanation generation), it is wrong. Empty states on the frontend; stub endpoints on the backend.

## Posture decisions (resolved during brainstorming, before §1)

| Decision | Choice | Constraints |
|---|---|---|
| Foundation gate | Local-first pragmatic | Carry-forward debt → `docs/decisions/` with trigger conditions; local substrate pinned production-faithful; K8s manifests authored but unapplied |
| Local Postgres | Docker `timescale/timescaledb:2.17.2-pg16` on `:5433` | Pinned tag (not `latest`); init script creates extension; `DATABASE_URL` flips to `:5433`; native PG18 left untouched |
| Calendar sync | Polling via APScheduler `AsyncIOScheduler` + `SQLAlchemyJobStore` | 5-min cadence per user; jitter via `hash(user_id) % 300s`; fenced Redis lock |
| Frontend data layer | React Query v5 (carried forward from Slice 0) | Existing — see `docs/decisions/2026-05-18-data-layer.md` |
| UUID strategy | Hybrid: v7 for hot tables (`behavior_events`, `tasks`, `mood_logs`, `energy_logs`); v4 cold | `uuid_utils` (Rust/PyO3) pinned exact; **v4 server default on every table** as fallback for raw SQL |
| JWT contract | Bearer-only, strict scheme parsing | Malformed `Authorization` → 401 `auth_invalid_scheme`; handoff text superseded |
| Slice 0 debt addressed this slice | A+C (migration hygiene), D (BFF `?id=` deletion) | B (outbox) and E (MCP namespace) deferred with explicit triggers |

---

## §1 — Substrate + carry-forward debt envelope

### Local substrate

`infra/dev/docker-compose.yml`:

- `postgres` service: image `timescale/timescaledb:2.17.2-pg16` (pinned tag, not `latest`). Published on host `:5433` to avoid collision with native PG18 on `:5432`. Command explicitly sets `shared_preload_libraries=timescaledb` (the upstream image preloads, but explicit beats inherited). Env: `TIMESCALEDB_TELEMETRY=off`. Healthcheck: `pg_isready -U lockin -d lockin_dev` interval 5s, retries 10, so dependent services can use `depends_on: condition: service_healthy`.
- `redis` service: `redis:7.4-alpine` on `:6379` (unchanged from Slice 0).
- `infra/postgres/init/01-timescale.sql` mounted to `/docker-entrypoint-initdb.d/` runs on container init: `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;`. Idempotent. **No `pgcrypto`** — `gen_random_uuid()` is a core builtin in PG13+ ([PG13 release notes](https://www.postgresql.org/docs/13/release-13.html)).

### Env wiring

- `.env.example` and `apps/api/.env.local.example` flip `DATABASE_URL` to `postgresql+asyncpg://lockin:lockin@localhost:5433/lockin_dev`. <!-- pragma: allowlist secret -->
- Test URL: `postgresql+asyncpg://lockin:lockin@localhost:5433/lockin_test`. <!-- pragma: allowlist secret -->
- Migration `0001` (TimescaleDB hypertable) is re-applied for real — the extension exists now. The local `alembic stamp 0001` workaround from the existing memory note is removed; the migration runs as written.

### Carry-forward debt envelope (Slice 0)

Folded into this slice:

- **A + C — Migration hygiene baseline.** Migration `0004_migration_hygiene_baseline.py` back-fixes `webauthn_credentials.id` and `tasks.id` to carry `server_default=text("gen_random_uuid()")`. Drops `ix_tasks_user_id`; creates `(user_id, created_at DESC, id DESC)`. The migration is the **server-side half of a paired change** — the matching `apps/api/app/db/models/task.py` edit (default flips from `uuid4` to `uuid_utils.uuid7`) lands in the same commit. The v4 server default is a *fallback for raw SQL*, not the truth of the table. Migration docstring spells this out so a future reader doesn't see v4 and assume the table is v4-everywhere. Standard is codified in `docs/decisions/2026-05-22-migration-standard.md`.
- **D — BFF `?id=` deletion debt.** `apps/web/src/app/api/tasks/[id]/route.ts` (route segment) replaces `apps/web/src/app/api/tasks/route.ts`'s query-param handling. Hook updated to call `/api/tasks/${id}`. Verified by existing Slice 0 deletion test.

Deferred with explicit triggers (recorded in `docs/decisions/2026-05-22-carry-forward-debt.md`):

- **B — Transactional outbox.** Trigger: *Before any deploy where the api runs on more than one instance, OR before staging cutover, whichever comes first. Local single-process dev is exempt.* Silent event drops are unobservable; "first incident" is a trigger that never fires.
- **E — MCP `app` namespace collision.** Trigger: Next slice that touches `apps/mcp/` for non-trivial work.

### Decision log to commit

- `docs/decisions/2026-05-22-local-substrate.md` — Docker pg16+timescale@5433; native PG18 untouched; pinned tag; init script for extension.

---

## §2 — Persistence layer

### Migration sequence

Each migration = one commit. Standard row shape codified in a `BaseEntity` SQLAlchemy mixin: `id`, `user_id`, `tenant_id` (nullable + indexed), `created_at`, `updated_at`, `version`. Each model inherits + adds its domain columns. A separate `UUIDv7Mixin` overrides `default=uuid_utils.uuid7` for hot tables.

| Rev | Purpose | Key changes |
|---|---|---|
| `0004` | Hygiene baseline (back-fix) | `webauthn_credentials.id` + `tasks.id` get `server_default=text("gen_random_uuid()")`. Drop `ix_tasks_user_id`, create `(user_id, created_at DESC, id DESC)`. **Paired with** `apps/api/app/db/models/task.py` edit: ORM default flips from `uuid4` to `uuid_utils.uuid7`. Docstring spells out the dual change. |
| `0005` | Tasks expansion | Adds `tenant_id UUID NULL` (indexed), `updated_at TIMESTAMPTZ DEFAULT now()` with `BEFORE UPDATE` trigger, `version INT NOT NULL DEFAULT 1`, `status VARCHAR(16) NOT NULL DEFAULT 'captured'` |
| `0006` | `schedule_slots` | `task_id` FK → tasks, `scheduled_for TIMESTAMPTZ`, `duration_minutes INT`. Standard cols. Index `(user_id, scheduled_for)`. v4 primary key. |
| `0007` | `mood_logs` | `logged_at TIMESTAMPTZ`, `score SMALLINT CHECK (score BETWEEN 1 AND 5)`, `note TEXT NULL`. Index `(user_id, logged_at DESC, id DESC)`. v7 primary key. |
| `0008` | `energy_logs` | Same shape as `mood_logs`. v7 primary key. |
| `0009` | `explanations` | `subject_type VARCHAR(32)`, `subject_id UUID`, `reasoning JSONB`, `model_id VARCHAR(64)`, `latency_ms INT`. Index `(user_id, created_at DESC, id DESC)`. v4 primary key. |
| `0010` | `calendar_events` | `google_event_id VARCHAR(1024)`, `summary TEXT`, `starts_at TIMESTAMPTZ`, `ends_at TIMESTAMPTZ`, `etag VARCHAR(64)`, `source_calendar_id VARCHAR(256)`. Unique `(user_id, google_event_id)`; index `(user_id, starts_at)`. v4 primary key. |
| `0011` | `oauth_tokens` (escalated table) | `user_id`, `provider VARCHAR(32)`, `refresh_token_encrypted BYTEA`, `access_token_encrypted BYTEA`, **`key_version SMALLINT NOT NULL DEFAULT 1`** (indexed), `access_token_expires_at TIMESTAMPTZ`, `granted_scopes TEXT[]`, `disconnected_at TIMESTAMPTZ NULL`, `refresh_failure_count INT NOT NULL DEFAULT 0`, `sync_token TEXT NULL`, `calendar_initial_sync_completed_at TIMESTAMPTZ NULL`. Unique `(user_id, provider)`. v4 primary key. Encryption: AES-GCM, keys from env (see §5). |
| `0012` | `idempotency_keys` | `(user_id, client_idempotency_key) UNIQUE`, `request_hash BYTEA`, `response_json JSONB`, `status_code SMALLINT`, `created_at`. **Born with `INDEX (created_at)`** for the batched cleanup pattern (see §4). v4 primary key. |
| `0013` | `behavior_events` hypertable + continuous aggregates | Create regular table → `create_hypertable('behavior_events', 'occurred_at', chunk_time_interval => INTERVAL '1 month')`. Compression: `ALTER TABLE … SET (timescaledb.compress, timescaledb.compress_segmentby = 'user_id, event_type'); SELECT add_compression_policy('behavior_events', INTERVAL '7 days')`. **Retention policy commented in DDL, not registered** (explicit). Two continuous aggs: `daily_task_completions` (count of `task.completed` events), `daily_mood_avg` (avg of `mood.logged` score). Refresh: `add_continuous_aggregate_policy(start_offset INTERVAL '7 days', end_offset INTERVAL '1 hour', schedule_interval INTERVAL '15 minutes')`. v7 primary key on regular events; hypertable partitioning by `occurred_at`. |
| `0014` | **Claim `apscheduler_jobs`** under Alembic management | APScheduler's `SQLAlchemyJobStore` creates `apscheduler_jobs` at runtime on first scheduler start; without explicit migration, the table sits outside the `alembic history` chain and confuses future readers. Migration body: `op.execute("CREATE TABLE IF NOT EXISTS apscheduler_jobs (id VARCHAR(191) PRIMARY KEY, next_run_time DOUBLE PRECISION, job_state BYTEA NOT NULL)")` + `CREATE INDEX IF NOT EXISTS ix_apscheduler_jobs_next_run_time ON apscheduler_jobs (next_run_time)`. Schema matches APScheduler source ([`apscheduler/jobstores/sqlalchemy.py`](https://github.com/agronholm/apscheduler/blob/3.x/apscheduler/jobstores/sqlalchemy.py)) — re-verify on any APScheduler bump. Downgrade drops the table. **Idempotent semantics (`IF NOT EXISTS`)** so the migration is safe whether APScheduler beat Alembic to the punch or not. |

### UUID strategy specifics

- **Library:** `uuid-utils` (Rust-backed via PyO3, ~10× faster than pure-Python alternatives, actively maintained). Pinned exact version in `apps/api/pyproject.toml`. **No hand-rolled v7 bit-packing anywhere** — bit layout bugs are silently destructive (corrupt time-ordering, invisible until index pages fragment in P2).
- **Hot tables (v7 mixin):** `behavior_events`, `tasks`, `mood_logs`, `energy_logs`.
- **Cold tables (v4):** `schedule_slots`, `calendar_events`, `explanations`, `idempotency_keys`, `oauth_tokens`, `webauthn_credentials`.
- Every table gets `server_default=text("gen_random_uuid()")` regardless of mixin — v4 server default is the safety net for raw SQL inserts; the ORM v7 default is the truth path.

### Seed script + Timescale validation

`apps/api/scripts/seed_behavior_events.py`:

- Generates 1,000,000 synthetic `behavior_events` rows across 90 days for 10 synthetic user UUIDs.
- Event types weighted: 40% `task.created`, 25% `task.completed`, 15% `mood.logged`, 10% `energy.logged`, 10% `task.modified`.
- Asserts the 30-day-task-completions continuous-aggregate query returns in <100ms post-refresh.
- Verifies compression engagement: backdates 1000 events into a chunk older than 7 days, calls `SELECT compress_chunk(c) FROM show_chunks(...) c` to force compression, asserts `chunks_detailed_size()` returns `before_compression > after_compression`.

### Decision log to commit

- `docs/decisions/2026-05-22-migration-standard.md` — UUID v7 hot / v4 cold; server-default v4 fallback; `(user_id, …_at DESC, id DESC)` index pattern; standard cols + `version` + `tenant_id` + `BEFORE UPDATE` trigger.

---

## §3 — Event spine (Redis Streams + consumer groups)

### Module + APIs

`apps/api/app/events/streams.py` extends Slice 0's `EventPublisher`. Three responsibilities, three classes:

#### `EventPublisher` (refactored API)

**Replaces** Slice 0's single `publish(event)` method with two typed methods — operational vs behavioral distinction **enforced in the type system, not comments**:

- `publish_behavioral(event)` — writes to stream **and** (Week 5+ consumer) enqueues hypertable insert into `behavior_events`. Used for: `task.created, task.completed, mood.logged, energy.logged, task.scheduled, task.accepted, task.rejected, task.modified`.
- `publish_operational(event)` — writes to stream only. Used for: `calendar.*, agent.action_*, system.*`.

Every `XADD` uses `MAXLEN ~ 100000` by default (configurable per-stream via constructor). The `~` allows approximate trimming (cheap O(1)). Prevents Redis-memory runaway when streams accumulate ahead of consumers being wired.

Stream entries carry `event_id` (sourced from the event envelope's existing `event_id`, a v7 UUID) — **not** a synthetic `idempotency_key`. Consumer-side dedup pattern is frozen in the module docstring:

> Consumers maintain a Redis set `consumer:<group>:seen` with 24h TTL per entry: `SADD consumer:<group>:seen <event_id> EX 86400 NX`. Check-then-add before processing. Separate keyspace from the streams themselves. **Week 5+ consumers inherit this pattern verbatim. Do not reinvent.**

Taxonomy of behavioral vs operational events is committed to `packages/events/README.md`.

#### `StreamRegistry`

Declarative list of `(stream_name, [consumer_groups])`. On api startup, calls `XGROUP CREATE … $ MKSTREAM` for each, catches `BUSYGROUP`. Idempotent.

```
events:tasks            → capture-svc, analytics-svc
events:mood_energy      → capture-svc, analytics-svc
events:calendar         → scheduler-svc, analytics-svc
events:agent            → agent-svc, analytics-svc
```

Plus 8 DLQ streams (per fix #2): `events:tasks:dlq:capture-svc`, `events:tasks:dlq:analytics-svc`, `events:mood_energy:dlq:capture-svc`, …, `events:agent:dlq:analytics-svc`. Each DLQ entry carries: `original_id, consumer_group, error_class, failure_reason, first_failure_at, last_failure_at, failure_count`.

#### `Reaper`

APScheduler job, every 60s, per `(stream, group)`. Walks `XPENDING events:<stream> <group> IDLE 300000 - + 100`; for each stuck entry, calls `XCLAIM events:<stream> <group> <original_consumer> 0 <entry_id> JUSTID IDLE 0`. **Reaper has no consumer name of its own** — it does not take ownership. Stuck messages become eligible for retry by the original consumer (which reads its own PEL via `XREADGROUP <group> <consumer> 0`).

The DLQRouter (next) owns the "too many retries" decision via delivery-count. Reaper just resets the clock.

#### `DLQRouter`

Wraps the (future) consumer's ack/nack. Logic: on `delivery_count > 3`, `XADD events:<stream>:dlq:<group>` with the original entry + the six debug fields, then `XACK` the source. Emits OTel counter `lockin.events.dlq.added{stream, group}`.

### Slice 0 stream backfill

Slice 0 emitted `task.created` entries without `event_id`. Pre-trim during §3 deploy as a one-line step in the deploy script:

```
XTRIM events:tasks MINID <unix-ms-at-§3-deploy>
```

Defensible: local-dev-only, no consumers exist yet, no real data loss.

### Metrics + alerting

- OTel counter `lockin.events.published{stream, event_type}`.
- OTel gauge `lockin.events.dlq.depth{stream, group}` — updated by Reaper via `XLEN events:<stream>:dlq:<group>`.
- Grafana alert rule authored in `infra/grafana/dashboards/event-spine.json` with threshold `dlq.depth > 10` per group. Rule import deferred to whenever Grafana UI authoring happens (per §1 deferral). Alert routes to `#lockin-test-alerts` (the channel from W1-2).

### Tests

- **`test_consumer_group_resumption`** (real Redis via testcontainers — fakeredis's `XINFO GROUPS` semantics diverge): produce 10k entries to `events:tasks`, stub consumer reads + acks 5k, restart, verify resumes at 5001 with no dups + no drops.
- **`test_dlq_routes_after_three_retries`** (fakeredis OK): 11 poisoned messages, stub consumer NACKs each 3×, verify `XLEN events:tasks:dlq:capture-svc == 11` and the depth metric exceeded 10.
- **`test_reaper_unit`** (fast, deterministic): mock `XPENDING`/`XCLAIM`, assert decision tree directly. Branch coverage.
- **`test_reaper_integration_slow`** (`@pytest.mark.slow`): real Redis, real `time.sleep(310)`, prove the wiring against Redis's actual clock. Runs in CI, not on every local push.

### Decision log to commit

- `docs/decisions/2026-05-22-event-publisher-typing.md` — `publish_behavioral` vs `publish_operational` enforced at the API surface; behavioral list pinned; operational list pinned; rationale = type-system prevents accidental pollution of behavior graph.

---

## §4 — API gateway middleware stack

### Six middlewares, one module each, at `apps/api/app/middleware/`

**Inbound order:** `ErrorEnvelope → RequestID → CORS → RateLimit → JWT → Idempotency → route`. ErrorEnvelope is **outermost** — wraps everything, including exceptions raised by other middlewares (a JWT parse failure → structured 500 envelope, never raw Starlette error page). Registered via `app.add_middleware()` in reverse of inbound order (Starlette wraps each call around the existing stack).

| # | Module | Behavior |
|---|---|---|
| 1 | `error_envelope.py` | **Outermost.** Catches `HTTPException` → `{error:{code, message, request_id}}`. Catches `Exception` → 500 envelope + `sentry_sdk.capture_exception`. Tracebacks never leak in prod (`ENV != "local"`). Always includes `request_id`. |
| 2 | `request_id.py` | Generate `uuid_utils.uuid7()` if `X-Request-Id` header absent. Set `contextvars.ContextVar` so OTel + log formatter pick it up. Echo in response header. |
| 3 | `cors.py` | Starlette `CORSMiddleware`. Origins from `WEB_ORIGINS` env (CSV). Local: `*`. Staging/prod: explicit list. |
| 4 | `rate_limit.py` | **Fixed-window counter** (not token bucket — accept 2×-burst-at-boundary tradeoff; P1 doesn't need burst smoothing). Lua at `apps/api/app/middleware/rate_limit.lua`: `local c = redis.call('INCR', KEYS[1]); if c == 1 then redis.call('EXPIRE', KEYS[1], 60) end; return c`. Loaded via `SCRIPT LOAD` on startup, `EVALSHA` at request, fallback to `EVAL` on `NOSCRIPT`. Per-user key `rl:user:{uuid}` (100/min), per-IP key `rl:ip:{addr}` (1000/min). On `redis.RedisError` or Lua returning `None`: log warning + Sentry breadcrumb + `return await call_next(request)` — **fail open is the only branch tested first.** |
| 5 | `jwt.py` | **Bearer-only, strict scheme parsing.** Reads `Authorization: Bearer <HS256>`. Anything else (`Token …`, `JWT …`, `bearer …` lowercase, missing scheme, missing header) → 401 with structured `error.code`. Codes: `auth_missing, auth_invalid_scheme, auth_invalid_signature, auth_expired, auth_malformed`. Lifted from Slice 0's `get_current_user` dependency. Anonymous paths allow-listed: `/health`, `/v1/auth/*`, `/docs`, `/openapi.json`. Attaches `request.state.user_id` (the deterministic `user_uuid()` v5 mapping from Slice 0). |
| 6 | `idempotency.py` | **Mutations only** (POST/PUT/PATCH/DELETE). No `Idempotency-Key` header → pass through, no caching. Canonical request hash: `sha256(method.upper() + path + querystring_sorted_by_key + body_normalized)` where JSON bodies are parsed and re-serialized with sorted keys (defeats false-positive 422s from key-order differences); non-JSON hashed as raw bytes. Hit + hash matches → replay cached `response_json` + `status_code`. Hit + hash differs → 422 `idempotency_key_reused`. Miss → capture response, write row **inside the same transaction as the route's writes** (no separate commit). **Cache only 2xx and 4xx** — 5xx never persisted (no row written); next retry re-executes the route. Module docstring documents this rule. **Session sharing wiring:** an upstream FastAPI dependency (`get_session_into_request_state`) attaches the async session to `request.state.db` before any route or middleware runs; both the idempotency middleware and the route's `Depends(get_session)` resolve to the same session object so the idempotency row joins the route's transaction without a second `commit()`. The dependency is wired in `apps/api/app/api/v1/deps.py` and applied via `app.dependency_overrides` so it's enforced globally, not per-route. |

### Stub endpoints (Week 5 needs these)

- `POST /v1/tasks` — already exists from Slice 0; idempotency now auto-applies (table exists). No new code.
- `POST /v1/mood` — new. `MoodLogCreate{score: int 1-5, note?: str, logged_at?: datetime}` → writes `mood_logs`, emits `mood.logged` via `publish_behavioral` to `events:mood_energy`.
- `POST /v1/energy` — identical shape, writes `energy_logs`, emits `energy.logged`.

### Idempotency TTL cleanup

APScheduler hourly job — **batched** to avoid lock storms at scale:

```
DELETE FROM idempotency_keys WHERE id IN (
  SELECT id FROM idempotency_keys
  WHERE created_at < now() - interval '24 hours'
  LIMIT 10000
)
```

Loop until zero rows affected. Each batch commits independently. Pattern reused for §5's sync-token cleanup. The `created_at` index (born with the table in migration `0012`) makes the `WHERE` clause an index scan.

### OpenAPI dump + CI gate

- `pnpm openapi:dump` script (repo root) invokes `python -c "import json; from app.main import app; print(json.dumps(app.openapi()))"`, writes `packages/shared-types/openapi.json`.
- **CI gate** in `.github/workflows/pr.yml`: runs `pnpm openapi:dump && git diff --exit-code packages/shared-types/openapi.json`. PR fails if dump produces a diff (developer forgot to regenerate). Kills "types are lying" bugs.
- Existing `pnpm typecheck` reads it via `openapi-typescript` for TS types.

### Tests (no theatre, just load-bearing behaviors)

- `test_error_envelope_catches_jwt_exception` — force JWT middleware to raise → response is structured 500 envelope, **not** Starlette default error page. Proves ErrorEnvelope-outermost ordering.
- `test_idempotency_replay_correctness` — same key + same body → identical response (byte-for-byte), single DB row. Same key + different body → 422.
- `test_idempotency_skips_5xx` — route raises 500 → no `idempotency_keys` row written → retry with same key re-executes the route.
- `test_rate_limit_fail_open_on_connection_error` — monkeypatch Redis to raise `ConnectionError` → request still 200 + Sentry breadcrumb captured.
- `test_rate_limit_fail_open_on_partial_failure` — mock Redis Lua call to return `None` → middleware fails open, logs warning, request proceeds.
- `test_jwt_structured_error_codes` — bad scheme → `auth_invalid_scheme`; expired token → `auth_expired`; missing → `auth_missing`. BFF needs these distinct codes (different recovery flows).
- `test_jwt_anonymous_paths` — `/health`, `/docs` open without auth; `/v1/tasks` without auth → 401 `auth_missing`.

### Decision log to commit

- `docs/decisions/2026-05-22-jwt-bearer-contract.md` — strict Bearer parsing; structured error codes; handoff text "cookie-based" is superseded by Slice 0's actual Bearer contract.

---

## §5 — Calendar OAuth + polling sync

### Scope extension + token storage

NextAuth Google provider config gains `https://www.googleapis.com/auth/calendar.readonly` in addition to existing `openid email profile`. Existing JWT-strategy sessions won't carry a calendar refresh token; the api can't read the BFF cookie under the Bearer-only contract.

**Therefore: new table `oauth_tokens`** (escalated per handoff rules; Md approved). Shape pinned in §2 migration `0011`.

**Encryption at rest:** AES-GCM, keys versioned via `key_version` column.

- Env: `OAUTH_TOKEN_ENCRYPTION_KEY_V1`, `OAUTH_TOKEN_ENCRYPTION_KEY_V2`, …
- App loads all defined versions on startup. Encrypts with `MAX(version)`. Decrypts using whichever version matches the row's `key_version` column.
- Rotation runbook (`docs/runbooks/oauth-token-encryption-key-rotation.md`): deploy V2 → background re-encrypt job updates each row from V1 to V2 → delete V1 env var once `MIN(key_version) = 2`. No outage window.
- Plaintext tokens never hit DB columns or logs.

### Re-consent UX

Existing users lack the calendar scope in their stored refresh token. Site-wide dismissible banner (`<Banner>` component, see §6) on `/today` and `/schedule` when calendar disconnected: "Connect Calendar to enable scheduling → /settings/integrations".

### Polling sync architecture

`AsyncIOScheduler` + `SQLAlchemyJobStore` (Postgres-backed — survives restarts; enables a second worker process in Week 5+ without rearchitecting). The jobstore's `apscheduler_jobs` table is brought under Alembic via migration `0014` (see §2) — no mixed-provenance schema.

One job per connected user: `sync_calendar({user_id})`, scheduled every 5min with `next_run_time = now() + (hash(user_id) % 300)s` for jitter.

Each job:

1. **Acquire fenced lock.** `SET lock:calendar:{user_id} <uuid7-token> EX 300 NX` — bail if held. Token stored on stack for release.
2. Load `oauth_tokens` row. Refresh access token if `expires_at - now() < 5min`.
3. **Inside `asyncio.timeout(280)`** (10s under the lock TTL — guarantees the release Lua runs before TTL expires, eliminating the lock-race window even on hangs): `GET https://www.googleapis.com/calendar/v3/calendars/primary/events?syncToken=<stored>&maxResults=250` (paginated).
4. Upsert each event into `calendar_events` keyed by `(user_id, google_event_id) UNIQUE`. Emit `calendar.event_synced` via `publish_operational` to `events:calendar` for new/changed rows.
5. Persist new `syncToken` on `oauth_tokens`.
6. **Release lock via Lua** (`apps/api/app/calendar/lock_release.lua`): `if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) else return 0 end`. Same `SCRIPT LOAD` → `EVALSHA` → fallback `EVAL` discipline as §4. **Prevents the lock-expired-then-deleted-by-late-job race.** Combined with the timeout in step 3, the worst-case behavior is `asyncio.TimeoutError` → release runs → next tick retries — never two concurrent jobs.

### Failure branches

- **`410 Gone`** (syncToken expired — typical after ~30 days inactivity or quota events) → drop `sync_token`, full re-sync `now()-7d` to `now()+30d`, persist new token. **After upserts, run orphan pruning in the same transaction:** `DELETE FROM calendar_events WHERE user_id = $1 AND google_event_id NOT IN (<set returned by full sync>)`. Logs count via OTel gauge `lockin.calendar.orphans_pruned{user_bucket}`.
- **`401 Unauthorized`** (user revoked) → `disconnected_at = now()`, emit `calendar.disconnected`, deregister the APScheduler job (don't keep retrying a dead user).
- **Transient HTTP errors** → exponential backoff within the 5-min window, max 3 retries; on final failure release lock + log + move on (next tick will retry).

### Token refresh job

Separate APScheduler job, **runs every minute on a bucketed subset of users** to prevent thundering-herd at scale:

```sql
SELECT * FROM oauth_tokens
WHERE disconnected_at IS NULL
  AND access_token_expires_at - now() < interval '24h'
  AND abs(hashtext(user_id::text)) % 60 = EXTRACT(MINUTE FROM now())::int
```

60 small batches per hour vs 1 large batch. Outbound Google calls capped via `asyncio.Semaphore(20)`. On refresh failure: increment `refresh_failure_count`, emit OTel counter `lockin.oauth.refresh_failures{provider}`. Grafana alert at >5/hr (rule JSON deferred per §1).

### Initial sync on connect

After OAuth consent, BFF redirects to `/settings/integrations?just_connected=calendar`. Frontend `POST`s `/v1/calendar/initial_sync` (idempotent via §4 middleware). api enqueues the APScheduler job with `next_run_time=now()`, returns `202`.

**Status reporting via SSE** (not polling):

`GET /v1/me/integrations/sync_status` returns `EventSourceResponse` from `sse-starlette`. Status sequence emitted:

```
started → fetching_events → events_received(N) → completed | failed(reason)
```

**Frontend cannot use the native browser `EventSource` API** — `EventSource` does not carry custom headers, and the BFF→api contract is Bearer-only. The frontend uses [`@microsoft/fetch-event-source`](https://github.com/Azure/fetch-event-source) (added to `apps/web/package.json`), which is `fetch`-based and accepts arbitrary headers including `Authorization: Bearer <token>`. Open on the `?just_connected=calendar` redirect; close on terminal event. No polling, no wasted requests, clear failure path.

### Disconnection / reconnection UX

`/settings/integrations` reads `/v1/me/integrations` → shows green check + `last_synced_at` when connected, "Reconnect" when `disconnected_at` set, "Connect calendar" when no row exists.

### Events emitted (not yet consumed)

- `calendar.connected`, `calendar.event_synced`, `calendar.disconnected` — all via `publish_operational` on `events:calendar`. **These are operational events; they do not feed `behavior_events` hypertable.** Calendar data from Google is ingested input, not user-emitted action. The type-system distinction in §3 makes this physically impossible to violate.

### Tests

- `test_initial_sync_persists_window` — mock Google API; verify events between `now-7d` and `now+30d` written; `calendar_initial_sync_completed_at` set.
- `test_incremental_sync_uses_syncToken` — first run uses time range; second run sends stored `syncToken`.
- `test_410_resync_prunes_orphans` — Google returns 410 → token dropped → full sync runs → events not in Google's response deleted from `calendar_events` (scoped to the user, in same txn as upserts).
- `test_401_marks_disconnected` — Google returns 401 → `disconnected_at` set, no future job runs, `calendar.disconnected` event on stream.
- `test_redis_lock_fencing_prevents_concurrent_sync` — simulate lock expiry mid-job: job A acquires, A hangs past TTL, B acquires (different token), A finishes and tries to release — Lua check rejects A's release; B's lock remains intact.

### Decision log to commit

- `docs/decisions/2026-05-22-calendar-sync.md` — polling via APScheduler+SQLAlchemyJobStore (Postgres-backed); 5-min cadence with hash jitter; fenced Redis lock; bucket-partitioned (60-way) token refresh; SSE for initial-sync status; `oauth_tokens` table escalation approval.

### Runbook

- `docs/runbooks/oauth-token-encryption-key-rotation.md` — disambiguated from OAuth `client_secret` rotation and Google refresh-token rotation (three different operations).

---

## §6 — Frontend shell

### Route structure (Next.js 16 App Router, route groups for layout isolation)

```
apps/web/src/
├── middleware.ts                          # auth gate; sanitize_next_param
├── lib/auth/redirect.ts                   # sanitize_next_param helper
├── app/
│   ├── layout.tsx                         # root: theme class from cookie + Accept-CH meta
│   ├── (auth)/login/page.tsx              # extends existing /login
│   ├── (authed)/
│   │   ├── layout.tsx                     # sidebar + bottom-tab + FAB shell; auth guard
│   │   ├── today/page.tsx                 # empty state + Cmd+K palette trigger
│   │   ├── schedule/page.tsx              # empty state ("Connect a calendar")
│   │   └── settings/
│   │       ├── layout.tsx                 # settings sub-nav
│   │       ├── page.tsx                   # theme toggle, account
│   │       └── integrations/page.tsx      # calendar connect, SSE consumer for sync status
```

**No `/onboarding` route in P1.** New users land on `/today`; the "Capture your first task" empty state IS the onboarding. Logged in `docs/decisions/2026-05-22-onboarding-deferred.md`. Route deferred to P2.

### Auth middleware + `sanitize_next_param`

`apps/web/src/lib/auth/redirect.ts` exports `sanitize_next_param(raw: string | null): string`:

- **Rule 0 (pre-check): reject any value containing `\`** before further validation. Browser URL normalization converts `\` → `/` in some contexts (a payload like `/\evil.com` becomes `//evil.com` after parsing), bypassing the protocol-relative check below. Standard OWASP open-redirect defense.
- Must start with `/` (single slash — `//` is protocol-relative, rejected).
- Must not start with `/api/`.
- URL-decoded form must also pass rules 0–2 (defeats double-encoding bypass).
- Any rule violation → drop param, return safe default `/today`.

Used in both `middleware.ts` (reading `?next=…`) and the login page (writing the `next` on the redirect URL). **Open-redirect class of vulnerabilities killed at the lib level.**

`middleware.ts` behavior:

- No session + path not in `[/login, /api/auth/*, /api/health]` → 302 `/login?next=<sanitized-current-path>`.
- Session + path = `/login` → 302 `sanitize_next_param(searchParams.get('next')) || /today`.
- Match config excludes `/_next/*`, `/favicon.ico`, static assets.

### Responsive layout (pure Tailwind, no JS breakpoint detection)

- `≥md`: collapsible left sidebar. Collapse state in `localStorage`, hydrated post-paint to avoid CLS.
- `<md`: **3-tab bottom nav** `[Today, Schedule, Settings]` + **FAB** for capture (fix #4).
- FAB component (`FloatingActionButton` in `@lockin/ui`): fixed `bottom-20 right-4` (clears tab bar), `aria-label="Capture"`, plus-icon, brand color.
- Header (both breakpoints): app title, **mood/energy widget slot** (placeholder `<div data-slot="mood-energy" />` for Week 5), user avatar menu.

### `@lockin/ui` additions

Extends Slice 0's `Input, Button, Stack, Text`. Each ships with a Storybook story in `packages/ui/src/<comp>/stories.tsx`:

- `Sidebar` — responsive container, collapse button, slots
- `BottomTabNav` — mobile-only, 3-slot (not 4 — see fix #4)
- `FloatingActionButton` — fixed position, icon + a11y label
- `EmptyState` — icon prop, title, body, primary action button
- `Banner` — dismissible, used for "Connect calendar" site-wide prompt
- `ThemeToggle` — sun/moon button, no flash
- `Skeleton` — loading state primitive

### Theme (no flash on SSR)

- Tailwind `darkMode: 'class'`.
- `apps/web/src/app/layout.tsx`:
  - Reads `theme` cookie server-side, applies `<html class={theme}>`.
  - Falls back to `Sec-CH-Prefers-Color-Scheme` request header if cookie absent.
  - Falls back to no class (system default) if neither present.
  - Includes `<meta http-equiv="Accept-CH" content="Sec-CH-Prefers-Color-Scheme">` so Chrome/Edge send the hint.
- `ThemeToggle` writes **both** `localStorage.theme` AND `document.cookie = 'theme=<value>; Path=/; Max-Age=31536000; SameSite=Lax' + (NODE_ENV === 'production' ? '; Secure' : '')`.
- No client-side `useEffect` hydration of theme class. **Server is the source of truth on first paint, with two fallback layers — flash branch eliminated.**

### Empty states + slots Week 5 needs

- `/today` → `<EmptyState title="Capture your first task" action="Open palette (⌘K)" />` + existing Slice 0 command palette wired to the action button. FAB on mobile triggers the same palette.
- `/schedule` → `<EmptyState title="Connect your calendar" action="Go to Integrations →" />` when disconnected; empty grid placeholder otherwise.
- Mood/energy header slot: `<div data-slot="mood-energy" />` placeholder.
- Site-wide `<Banner>` on `/today` and `/schedule` when calendar disconnected.

### Palette focus management

Radix `Dialog` with:

- Default `onOpenAutoFocus` — input receives focus on open.
- Default `onCloseAutoFocus` — focus returns to the element that triggered open.
- Test `test_palette_focus_returns_to_trigger`: open via empty-state button, close via Escape, assert `document.activeElement === triggerButton`. axe-core won't catch this; integration test required.

### Error boundaries + loading

Next 16 idioms: `error.tsx` at each route segment, `loading.tsx` for Suspense fallback. Data fetches use React Query `isPending` (Slice 0 pattern).

### A11y

- Skip-to-content link as first focusable element in `(authed)/layout.tsx`.
- Focus rings via Tailwind `focus-visible:` — never disabled.
- All interactive elements have keyboard handlers (no `onClick`-only `<div>`s).
- `apps/web/src/tests/a11y.test.tsx` — renders each route's static empty state, runs `vitest-axe`, asserts zero violations. Runs every commit.

### Lighthouse CI

`.lighthouserc.json`:

```json
{
  "assertions": {
    "categories:performance": ["error", {"minScore": 0.85}],
    "categories:accessibility": ["error", {"minScore": 0.95}],
    "categories:best-practices": ["error", {"minScore": 0.90}],
    "categories:seo": ["error", {"minScore": 0.90}]
  },
  "numberOfRuns": 1
}
```

Per-category gates, not aggregate. Accessibility gets the highest threshold (silent compounding regressions). **Retry count = 1** — flakiness investigated, not papered over. If PR friction emerges, alternative is to split Lighthouse to a post-merge `main` workflow and gate PRs on a11y + best-practices only (defer this decision).

### Tests

- `test_middleware_redirects_unauthed` — no session + `/today` → 302 `/login?next=/today`.
- `test_middleware_redirects_authed_from_login` — session + `/login?next=/settings` → 302 `/settings`.
- `test_middleware_rejects_malicious_next` — `//evil.com`, `https://evil.com`, `/api/auth/csrf`, `%2F%2Fevil.com`, `%252F%252Fevil.com`, `/\evil.com`, `%5Cevil.com` all sanitized to `/today`.
- `test_theme_persists_across_refresh` — toggle → reload → class still applied; no flash (assert `<html>` class on first paint, not post-hydrate).
- `test_today_empty_state_opens_palette` — clicking action triggers palette open.
- `test_palette_focus_returns_to_trigger` — Escape → focus on trigger button.
- `test_a11y_zero_violations` — every empty-state route renders axe-clean.
- Lighthouse CI in pipeline; not a vitest test.

### Decision log to commit

- `docs/decisions/2026-05-22-onboarding-deferred.md` — no `/onboarding` route in P1; empty states are the onboarding; route deferred to P2.

---

## §7 — Sequencing, DoD, handoff to Week 5-6

### PR mechanics

Single branch `feat/week-3-4-scaffolding`. One PR. Six logical commits (one per deliverable). Squash-merge. Matches handoff + Slice 0 precedent.

### Day-by-day plan (solo, sequential by dependency)

| Day | Work | Verifies |
|---|---|---|
| 1 | §1 substrate (Docker pg16+timescale@5433, healthcheck, init script). §2 migrations `0004` (hygiene baseline, paired ORM edit) + `0005` (tasks expansion). `BaseEntity` mixin + `UUIDv7Mixin` in place | `alembic upgrade head && downgrade base && upgrade head` is a no-op; v4 server default + v7 ORM default coexist |
| 2 | §2 migrations `0006-0010` (schedule_slots, mood_logs, energy_logs, explanations, calendar_events) | All standard cols + indexes ship; `EXPLAIN ANALYZE` shows index scans on `(user_id, …_at DESC, id DESC)` |
| 3 | §2 migrations `0011` (oauth_tokens, key_version), `0012` (idempotency_keys + created_at index), `0013` (behavior_events hypertable + 2 continuous aggs + compression policy). 1M-event seed script | Aggregate query <100ms; `compress_chunk` engages on backdated chunk |
| 4 | §3 `EventPublisher` refactor (`publish_behavioral`/`publish_operational`, `MAXLEN ~ 100000`, `event_id` field). `StreamRegistry` (4 streams + 4 groups + 8 DLQ streams). `Reaper` (`XCLAIM JUSTID IDLE 0`). `DLQRouter`. Slice 0 `XTRIM` | Streams + groups idempotent on restart; reaper unit test passes; DLQ shape correct |
| 4–5 boundary | **Mid-slice review with Md (15 min screenshare).** Walk §1+§2 deliverables against DoD. Two outcomes: green → §3; red → scope cut decided live | Surface slip with 5 days runway, not 4 |
| 5 | §3 integration tests (real Redis via testcontainers): `test_consumer_group_resumption`, DLQ routing, `test_reaper_integration_slow` | All §3 tests green |
| 6 (AM) | **§6 scaffolding split** (conditional, 3hr max): scaffold route groups in `(auth)/` + `(authed)/`, drop `EmptyState`/`Banner`/`Skeleton`/`FAB` into `@lockin/ui` with Storybook stories, write `sanitize_next_param` + tests. Skip if Day 4–5 review shows ahead | Pulls ~30% of §6 forward into low-pressure time; leaves Day 10 for integration work |
| 6 (PM)–7 | §4 middleware stack (6 modules). ErrorEnvelope outermost (with the forced-JWT-raise test). Strict Bearer JWT with structured `error.code`. Rate-limit Lua via `SCRIPT LOAD`+`EVALSHA`. Idempotency 2xx/4xx-only + canonical hash | Order test passes; rate-limit fails open on both error types; idempotency replays + 422s correctly |
| 7 | §4 stub endpoints `/v1/mood`, `/v1/energy`. Idempotency TTL cleanup (batched). OpenAPI dump script + CI `git diff --exit-code` gate | Three load-bearing tests green; CI catches missing dump regeneration |
| 8 | §5 calendar scope extension, `oauth_tokens` AES-GCM encryption (V1 key only), migration `0014` (Alembic-claim `apscheduler_jobs`), APScheduler polling with fenced lock + `asyncio.timeout(280)`, 410+401 branches with orphan pruning, token refresh with 60-bucket partition + `Semaphore(20)` | Mocked-Google integration tests green; lock fencing test passes; `alembic history` shows 0014 in the chain |
| 9 | §5 SSE for initial-sync status (backend `EventSourceResponse` + frontend `@microsoft/fetch-event-source` consumer for Bearer compatibility). Re-consent banner. `/settings/integrations` connect flow. 5 calendar tests | All §5 tests green |
| 10 | §6 integration work: theme cookie + CH-hint + Secure flag, FAB wiring, palette focus-return, route guard with `sanitize_next_param`, Lighthouse CI tuning, vitest-axe. **Execute end-to-end smoke test (`docs/handoffs/week-3-4-smoke-test.md`).** Final DoD walkthrough | All six DoD groups green; spec doc + handoff written; smoke green |

### Dependency graph

```
§1 substrate ──► §2 persistence ──► §3 event spine ──► §4 middleware ──► §5 calendar
                                                            │
                                                            └─► §6 frontend (depends only on §4 endpoints existing)
```

Day 6 AM scaffolding split pulls §6 work that doesn't depend on `/v1/mood` or `/v1/energy` forward; Day 10 handles the rest.

### Definition of Done

Every row must pass before squash-merge.

#### Persistence

- [ ] `alembic upgrade head && alembic downgrade base && alembic upgrade head` clean and idempotent
- [ ] `EXPLAIN ANALYZE` snapshots for three indexed queries committed at `docs/architecture/explain-snapshots.md` (tasks-by-user, mood-by-user, calendar-by-user-time)
- [ ] Schema diagram auto-generated via `eralchemy2` from SQLAlchemy metadata at `docs/architecture/schema-w3-4.svg`

#### Timescale

- [ ] 1M-event seed runs to completion
- [ ] 30-day continuous-aggregate query <100ms post-refresh
- [ ] Force-compressed chunk verified via `chunks_detailed_size()` showing before > after

#### Event spine

- [ ] Real-Redis `test_consumer_group_resumption` green
- [ ] DLQ entries carry all six debug fields + per-(stream, group) split
- [ ] Reaper unit + slow integration tests both green
- [ ] Grafana DLQ alert rule JSON committed at `infra/grafana/dashboards/event-spine.json`
- [ ] `MAXLEN ~ 100000` default verified via `XLEN` on a flooded stream
- [ ] `publish_behavioral` vs `publish_operational` API enforced; calendar.* cannot be published via behavioral path (type error)

#### Middleware

- [ ] ErrorEnvelope-outermost test (forced JWT raise → structured 500)
- [ ] Idempotency 2xx/4xx-only test (5xx not cached); canonical hash test (key reorder no false 422)
- [ ] Rate-limit fail-open on `ConnectionError` AND on `None` reply
- [ ] JWT structured `error.code` test (5 codes covered)
- [ ] OpenAPI CI gate: `pnpm openapi:dump && git diff --exit-code` runs in PR pipeline

#### Calendar

- [ ] Scoped OAuth flow extension; banner appears for users without calendar scope
- [ ] Mock-Google initial sync persists 14d window
- [ ] 410 → full re-sync + orphan pruning; metric `lockin.calendar.orphans_pruned` increments
- [ ] 401 → `disconnected_at` set + `calendar.disconnected` emitted; APScheduler job deregistered
- [ ] Fenced-lock concurrency test green
- [ ] Key-rotation runbook at `docs/runbooks/oauth-token-encryption-key-rotation.md`

#### Frontend

- [ ] All 5 routes render correctly desktop + mobile (Slow 4G via Lighthouse)
- [ ] Per-category Lighthouse gates pass: Perf 0.85, A11y 0.95, BP 0.90, SEO 0.90
- [ ] `vitest-axe` zero violations on every empty-state route
- [ ] `sanitize_next_param` rejects all five malicious cases
- [ ] Palette focus-return test passes
- [ ] Theme no-flash test (first-paint `<html>` class set correctly with cookie absent + CH hint present)

#### End-to-end smoke test (Day 10 gate)

- [ ] `docs/handoffs/week-3-4-smoke-test.md` exists and all 10 steps execute cleanly against local-first substrate

#### Meta

- [ ] `docs/CURRENT_SLICE.md` rewritten → Week 5-6 capture loop
- [ ] `docs/handoffs/week-3-4.md` written (what shipped, what was punted, what Week 5 needs to know)
- [ ] All 7 decision logs committed (see below)

### End-to-end smoke test scenario

`docs/handoffs/week-3-4-smoke-test.md` — 10 numbered steps, each with an observable outcome. Executed Day 10 as final integration gate; doubles as Week 5–6 regression checklist.

1. Fresh OAuth login as a new user → JWT cookie set, `user_uuid()` computes deterministic UUID5 from Google `sub`.
2. Navigate to `/settings/integrations` → "Connect calendar" button visible (no `oauth_tokens` row for user).
3. Complete calendar OAuth → `oauth_tokens` row exists with `key_version=1`, AES-GCM-encrypted refresh token, `granted_scopes` includes `calendar.readonly`.
4. SSE on `/v1/me/integrations/sync_status` fires `completed` within 60s → `calendar_events` has ≥1 row for the user.
5. `POST /v1/tasks` with `Idempotency-Key: abc123` and a valid body → 201, `tasks` row with v7 UUID, `task.created` entry on `events:tasks` with `event_id` matching the row.
6. Same `POST /v1/tasks` with same key + same body → 201, byte-identical response, single `tasks` row (idempotency hit verified via `SELECT count(*)`).
7. Same key with different body → 422 `idempotency_key_reused`.
8. `XLEN events:tasks` shows entries; `XLEN events:tasks:dlq:capture-svc` shows 0.
9. Force Redis down via `docker compose stop redis` → `POST /v1/tasks` still returns 200 (rate-limit fails open; verify Sentry breadcrumb).
10. `pnpm lighthouse` against `/today` → all four category gates pass.

### Decision logs to commit (7 total)

1. `docs/decisions/2026-05-22-local-substrate.md`
2. `docs/decisions/2026-05-22-migration-standard.md`
3. `docs/decisions/2026-05-22-carry-forward-debt.md`
4. `docs/decisions/2026-05-22-calendar-sync.md`
5. `docs/decisions/2026-05-22-jwt-bearer-contract.md`
6. `docs/decisions/2026-05-22-event-publisher-typing.md`
7. `docs/decisions/2026-05-22-onboarding-deferred.md`

### Runbooks created this slice

- `docs/runbooks/oauth-token-encryption-key-rotation.md`

### What Week 5-6 inherits

1. **Endpoints** — `POST /v1/tasks`, `POST /v1/mood`, `POST /v1/energy`. All accept `Idempotency-Key`. All emit via `publish_behavioral`. Week 5 wires consumers; the hypertable insert path is one line: register the consumer.
2. **Streams + groups exist, no consumers running.** `capture-svc` + `analytics-svc` pre-created on `events:tasks` and `events:mood_energy`; `MAXLEN ~ 100000` cap prevents memory runaway in the meantime.
3. **`calendar_events` populated** for any connected user — proves end-to-end ingestion.
4. **`/today` empty state + Cmd+K button** — palette exists from Slice 0; button wires to `palette.open()`. Mobile FAB triggers same. **Mood/energy widget slot** is a placeholder `<div data-slot="mood-energy" />` in the header — Week 5 swaps in the real widget.
5. **Storybook contains every empty state + the shell** so Week 5 iterates on populated states without re-scaffolding.
6. **React Query + BFF route patterns established** — Slice 0's `/api/tasks` is the template for `/api/mood`, `/api/energy`, and any future BFF route.

---

## Carry-forward debt (with triggers)

| Debt | Trigger |
|---|---|
| Transactional outbox for event-emitting mutations | Before any deploy where the api runs on more than one instance, OR before staging cutover, whichever comes first. Local single-process dev is exempt. |
| MCP `app` package-name collision (`apps/api` + `apps/mcp` both install as `app`) | Next slice that touches `apps/mcp/` for non-trivial work. |
| Calendar webhooks (push notifications) | P2 conversation. P1 is polling-only. |

## Out of scope (do not let these sneak in)

- Scheduling algorithm
- Mood/energy widget *interaction* (slot only)
- LLM calls
- Explanation generation logic
- Bidirectional calendar sync (read-only this slice)
- New OAuth providers (Apple/Microsoft are Week 5 polish)
- Native mobile
- Gamification / streaks / badges
- 5-tier productivity classification
- Team features / RLS policies (`tenant_id` is nullable + indexed; no policies yet)
- Webhooks for anything
- Temporal (Week 9–10)
- Analytics dashboard / `/insights` route
- `/onboarding` route (deferred to P2)

---

## Next steps (post-spec approval)

1. ✅ Spec written + committed (this commit) — artifact in git history before review
2. Spec self-review by Claude Code → produces 4–6 line written checklist of actual findings (not "I reviewed it")
3. Md reads spec end-to-end against the bend messages; comments inline; approves or revises
4. Invoke `superpowers:writing-plans` to produce implementation plan from approved spec
