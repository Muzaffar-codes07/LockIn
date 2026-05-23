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
