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
