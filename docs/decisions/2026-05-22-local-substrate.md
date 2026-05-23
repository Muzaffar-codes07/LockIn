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
