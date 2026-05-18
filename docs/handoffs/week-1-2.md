# Week 1–2 Foundation — Handoff to Week 3

**Slice status:** ✅ **COMPLETE** — all 8 deliverables merged to `main` (2026-05-18)
**Plan:** [`docs/superpowers/plans/2026-05-11-week-1-2-foundation.md`](../superpowers/plans/2026-05-11-week-1-2-foundation.md)
**Shipped via:** PRs #1–#5

## Delivery map

| PR | Branch | Deliverables |
| --- | --- | --- |
| #1 | `feat/week-1-2-foundation` | 1 Monorepo · 2 CI (PR pipeline) · 3 Terraform · 7 design system · 8 event schema |
| #2 | `feat/auth-google-oauth` | 6 Auth foundation · TimescaleDB hypertable migration |
| #3 | `feat/observability-baseline` | 4 Observability (OTel + Sentry + Grafana) |
| #4 | `feat/deploy-and-secrets` | 2 CI (staging/prod CD) · 5 Secret management |
| #5 | `feat/storybook-preview` | 7 Storybook deploy |

## Acceptance vs current state

| # | Deliverable | Acceptance check | State |
| --- | --- | --- | --- |
| 1 | Monorepo | `pnpm install` + `pnpm dev` boots web; `make api`/`make mcp` boot the Python apps | ✅ shipped |
| 2 | CI/CD | PR pipeline (paths-filtered) + `staging.yml` + `prod.yml` | ✅ shipped — live deploys gated on repo secrets |
| 3 | Terraform | GCP modules (vpc/postgres/redis/gke/secrets/dns) + staging/prod envs | ✅ shipped — `apply` pending one-time GCP bootstrap |
| 4 | Observability | OTel + Sentry on api/mcp/web; Grafana dashboards; forced-500 route | ✅ shipped — Grafana UI authoring + Slack contact point pending |
| 5 | Secrets | Zero secrets in repo; `pnpm secrets:pull` helper | ✅ shipped |
| 6 | Auth foundation | NextAuth v5 + Google OAuth + JWT middleware + `/api/me`; WebAuthn passkey endpoints | ✅ shipped |
| 7 | Design system | `@lockin/ui` 6 base components + tokens; `apps/web` consumes them; Storybook | ✅ shipped — Lighthouse ≥95 verify pending live deploy |
| 8 | Event schema v1 | 9 event types, TS↔Python round-trip; TimescaleDB migration ready (unapplied) | ✅ shipped |

## Test posture on `main`

- `pnpm typecheck` — 5/5 turbo tasks · `pnpm lint` — 3/3 · `pnpm test` — 18 ui + 19 events
- `pytest apps/api` — 15 · `pytest apps/mcp` — 2 · `pytest packages/events` — 10
- `mypy apps/api` clean (40 files) · `mypy apps/mcp` clean (12 files)

## Open operational debt — must be done before staging is real

These are **not code** — they are one-time provisioning steps, owned by DevOps:

- **GCS state bucket** — `gcloud storage buckets create gs://lockin-tfstate-$LOCKIN_GCP_PROJECT …` (see [`infra/terraform/README.md`](../../infra/terraform/README.md)).
- **GitHub Actions OIDC → GCP** — create the Workload Identity Federation pool/provider; bind the `lockin-deploy` service account. Cannot be Terraformed (chicken-and-egg).
- **Repo secrets** — provision `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_WEB_PROJECT_ID`, `VERCEL_STORYBOOK_PROJECT_ID`, `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_DEPLOY_SA`, `GCP_PROJECT_ID`, `SENTRY_DSN_*`, `SENTRY_ORG/PROJECT/AUTH_TOKEN`, `GRAFANA_CLOUD_OTLP_*`.
- **`prod` GitHub Environment** — configure Required reviewers in repo Settings → Environments. The `prod.yml` workflow references the environment but does not enforce the gate by itself.
- **TimescaleDB** — after the first `terraform apply` provisions Cloud SQL, run `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;` once, then apply Alembic migration `0001`.
- **K8s manifests** — `staging.yml`/`prod.yml` assume `Deployment/api` and `Deployment/mcp` already exist in the `lockin` namespace. Authoring those manifests is the first infra task of whichever slice ships the backend to GKE.
- **Grafana** — import the three dashboards from [`infra/grafana/dashboards/`](../../infra/grafana/dashboards), create the `#lockin-test-alerts` Slack contact point + the `api 5xx > 0` rule, then run the forced-500 acceptance test (`curl …/v1/__debug__/force_500`).

## Known code follow-up

- **`app` package-name collision** — both `apps/api` and `apps/mcp` install themselves as the top-level `app` Python module. The `apps/mcp` smoke test works around it with `importlib` path-loading. Proper fix: rename one package (`refactor/mcp-namespace`). Not foundation scope.

## What Week 3 (Auth + Task Capture Spine) starts with

- A user can sign in with Google; `/api/me` returns `{ user_id, email, providers }`.
- The api validates a shared-secret HS256 bearer (`get_current_user` dependency) and can write to Postgres.
- The event schema imports cleanly from `apps/web` (`@lockin/events`) and `apps/api` (`lockin_events`).
- `@lockin/ui` exports `Input`, `Button`, `Stack`, `Text` — everything the task-input UI needs.
- Sentry catches errors; OTel traces flow once `GRAFANA_CLOUD_OTLP_*` is set; the forced-500 route proves the chain.
- `docker compose -f infra/docker/docker-compose.dev.yml up -d` brings up local Postgres + Redis.

## What Week 3 should NOT do

- Re-touch monorepo wiring, the event-schema codegen pipeline, or `@lockin/ui` base components — extend only.
- Add another OAuth provider — Apple + Microsoft are the Week 5 polish window ([`docs/decisions/2026-05-11-cloud-and-oauth.md`](../decisions/2026-05-11-cloud-and-oauth.md)).
- Start gamification, native mobile, or an analytics dashboard — out of P1 scope per `CLAUDE.md`.
