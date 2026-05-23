# Event publisher typing: behavioral vs operational at the API surface

**Date:** 2026-05-22
**Status:** Accepted

## Decision

`EventPublisher` exposes two methods, not one:
- `publish_behavioral(event)` — writes to the Redis Stream AND (Week 5+) the consumer enqueues a `behavior_events` hypertable insert.
- `publish_operational(event)` — writes to the Redis Stream only. Never pollutes the behavior graph.

Callers MUST pick the typed method at the call site. There is no generic `publish(event)`.

## Why

Calendar events from Google are ingested data, not user actions; routing them into `behavior_events` would corrupt the long-tail behavioral dataset that is the product's moat. Comment-only conventions don't survive review churn. Enforcing the distinction at the API surface makes accidental mis-routing impossible at compile time (in spirit; Python is dynamic, but mypy + ruff catch it).

## Taxonomy

**Behavioral:** `task.created, task.completed, task.scheduled, task.accepted, task.rejected, task.modified, mood.logged, energy.logged`

**Operational:** `calendar.connected, calendar.event_synced, calendar.disconnected, agent.action_proposed, agent.action_committed, system.*`
