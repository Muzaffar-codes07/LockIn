# Week 1–2 Foundation — Handoff to Week 3

**Date:** 2026-05-11
**Branch:** `feat/week-1-2-foundation`
**Plan:** [`docs/superpowers/plans/2026-05-11-week-1-2-foundation.md`](../superpowers/plans/2026-05-11-week-1-2-foundation.md)

This slice is partially landed. The foundation-unblocking subset that Week 3 depends on is shipped; auth, observability, and Storybook are sequenced for follow-up sessions.

## Shipped this session

- [x] **Deliverable 1 — Monorepo.** Turborepo + pnpm workspace at root. `pnpm install && pnpm typecheck` green on a clean clone. 4 workspaces: `@lockin/web`, `@lockin/events`, `@lockin/ui`, `@lockin/shared-types`. uv workspace covers `apps/api`, `apps/mcp`, `packages/events/python`.
- [x] **Deliverable 2 — CI/CD (PR pipeline).** `.github/workflows/pr.yml` with `dorny/paths-filter` for changed-package detection. Separate jobs: js (lint/typecheck/test/build), python-api (ruff/mypy/pytest), python-mcp, events-roundtrip (TS + Python parity), terraform-plan (fmt-check + validate staging + prod). One `gate` job aggregates results so branch protection has a single required check.
- [x] **Deliverable 3 — Terraform (modules + envs).** Six GCP modules (`vpc`, `postgres`, `redis`, `kubernetes`, `secrets`, `dns`) wired into `envs/staging` and `envs/prod`. GCS remote state, env-prefixed paths. README documents state-bucket bootstrap, TimescaleDB `CREATE EXTENSION` step, and the Workload Identity Federation chicken-and-egg.
- [x] **Deliverable 7 — Design system (`@lockin/ui`).** Six base components (`Button`, `Input`, `Card`, `Stack`, `Text`, `Icon`) + Tailwind v4 `@theme` token block with brand, semantic surfaces, type scale, spacing, motion, radius, dark-mode variants. 18 component tests via Vitest + Testing Library. `apps/web` consumes `@lockin/ui` and the page renders `Button/Stack/Text` — design-system smoke test green.
- [x] **Deliverable 8 — Event schema v1.** Zod source-of-truth at `packages/events/src/schema.ts`. 9 event types (`task.created`, `task.scheduled`, `task.accepted`, `task.rejected`, `task.modified`, `task.completed`, `mood.logged`, `energy.logged`, `schedule.explained`). Versioned envelope (`event_version: 1`) with `source` enum, `tenant_id`, `client_idempotency_key`. JSON Schema emitted; pydantic models generated via `datamodel-code-generator`. 19 TS round-trip tests + 10 Python round-trip tests — both green. `apps/api/app/events/schemas.py` rewritten to thin re-export from the `lockin_events` package.

## Punted to follow-up sessions

- [ ] **Deliverable 2 — staging + prod pipelines.** `.github/workflows/staging.yml` and `prod.yml` are speced in the plan (Task 6) but not committed. Manual reviewer approval on the `prod` GitHub Environment is a repo-setting and is **not** enforced by the workflow file alone.
- [ ] **Deliverable 4 — Observability.** OpenTelemetry SDK wiring (Task 11), Sentry SDK on web/api/mcp (Task 12), Grafana Cloud dashboards + Slack alert + forced-500 verification (Task 13). Today's `apps/api/app/core/logging.py` is OTel-compatible structured logging only — no exporter yet.
- [ ] **Deliverable 5 — Secret management.** `scripts/secrets-pull.mjs` and `.env.example` expansion (Task 8). Today there are no real secrets in the repo (✓) but no automated rotation pull either.
- [ ] **Deliverable 6 — Auth foundation.** NextAuth v5 + Google OAuth + JWT middleware + `/api/me` (Task 9), WebAuthn passkey endpoints (Task 10).
- [ ] **Deliverable 7 — Storybook deploy** (Task 4). Components exist; Storybook config + Vercel preview workflow do not.
- [ ] **Deliverable 8 — TimescaleDB hypertable migration** (Task 14). Alembic migration not yet committed; the plan has the code.

## Open infra debt (must do once, manually, before staging is real)

- Create GCS state bucket: `gcloud storage buckets create gs://lockin-tfstate-$LOCKIN_GCP_PROJECT ...` (see [`infra/terraform/README.md`](../../infra/terraform/README.md)).
- Configure GitHub Actions OIDC → GCP Workload Identity Pool. The pool/provider isn't in Terraform — it would have to authenticate as itself to create itself.
- After Terraform applies Cloud SQL: connect once and run `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;`.
- Configure repo Settings → Environments → `prod` with required-reviewers; the workflow file does not enforce this on its own.

## What Week 3 (Auth + Task Capture Spine) starts with

- `pnpm install && pnpm dev` boots `@lockin/web` on `http://localhost:3000`.
- `@lockin/web` already imports `Button`, `Stack`, `Text` from `@lockin/ui`. Adding `Input` for the task-input field is one import.
- `@lockin/events` exports `TaskCreatedEvent`, `LockInEvent`, and 7 more event types. `apps/api` imports the same types via `from lockin_events import TaskCreated`.
- The `events:tasks` Redis stream constant is canonical in both languages. `EVENT_TYPE_TO_STREAM["task.created"] === "events:tasks"`.
- `apps/api` test suite still passes after the `schemas.py` rewrite — 1 health test green.
- `docker compose -f infra/docker/docker-compose.dev.yml up -d` brings up local Postgres + Redis (this slice did not touch local-dev infra).

## What Week 3 should **not** do

- Touch root Turborepo wiring, event schema TS/Python codegen pipeline, or `@lockin/ui` base components. Add new components/events only if needed.
- Add another OAuth provider — that's the Week 5 polish window per the cloud + OAuth decision record ([`docs/decisions/2026-05-11-cloud-and-oauth.md`](../decisions/2026-05-11-cloud-and-oauth.md)).
- Start native mobile, gamification, or analytics dashboard work — those are P3 / out-of-scope per `CLAUDE.md`.

## Acceptance vs current state

| #   | Deliverable                              | Acceptance check                                            | State                                     |
| --- | ---------------------------------------- | ----------------------------------------------------------- | ----------------------------------------- |
| 1   | Monorepo                                 | `pnpm install && pnpm dev` boots all 3 apps from clean clone | ✓ shipped                                 |
| 2   | CI/CD                                    | PR pipeline runs only changed-package tests; main→staging <8m; tag→prod with approval | PR pipeline ✓ shipped; staging/prod ↺ punted |
| 3   | Terraform                                | `apply` from zero produces working staging; `destroy` clean | ✓ shipped (validation pending real `apply`) |
| 4   | Observability                            | Forced 500 → Sentry + Grafana + Slack alert within 60s      | ↺ punted                                  |
| 5   | Secrets                                  | No secrets in repo; rotation without redeploy               | Half: repo is clean (✓), no rotation tool yet |
| 6   | Auth foundation                          | OAuth signin → `/api/me` returns user; passkey verify works | ↺ punted                                  |
| 7   | Design system                            | `@lockin/web` uses `@lockin/ui`; Lighthouse ≥95             | Components ✓ shipped; Storybook deploy ↺ punted |
| 8   | Event schema v1                          | TS↔Python round-trip green; hypertable migration ready      | Round-trip ✓ shipped; migration ↺ punted  |

## Pointer for the next session

Read [`docs/superpowers/plans/2026-05-11-week-1-2-foundation.md`](../superpowers/plans/2026-05-11-week-1-2-foundation.md) — Tasks **4, 6, 8, 9, 10, 11, 12, 13, 14** are concretely spec'd and unexecuted. Each has full code/config; no placeholders.
