# Week 1–2 Foundation Slice — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the eight Week 1–2 Foundation Handoff deliverables — monorepo wiring, CI/CD, GCP Terraform, observability, secret management, auth foundation, design system, and event schema v1 — so the Week 3 Auth+Task-Capture vertical slice can start clean on Day 1.

**Architecture:** Turborepo at the repo root orchestrates three apps (`apps/web` Next.js 16, `apps/api` FastAPI/uv, `apps/mcp` MCP server/uv) and three packages (`@lockin/events`, `@lockin/shared-types`, `@lockin/ui`). The event schema is canonical in Zod under `packages/events/src/schema.ts`; TypeScript types are native; Python pydantic models are code-generated from emitted JSON Schema via `datamodel-code-generator`. GCP is the cloud (Cloud SQL Postgres 16 + TimescaleDB, Memorystore Redis, GKE, Secret Manager, GCS state). Auth is NextAuth v5 with Google-only OAuth and WebAuthn passkey registration. Observability is OpenTelemetry → Grafana Cloud + Sentry. CI/CD is GitHub Actions with three pipelines (PR, main→staging, tag→prod).

**Tech Stack:** Turborepo, pnpm 9, Node 20, Next.js 16, React 19, Tailwind v4, TanStack Query, Zustand, NextAuth v5, `@simplewebauthn/{server,browser}`, Storybook 8, FastAPI, Python 3.12, uv, Pydantic 2, SQLAlchemy 2 async, Alembic, `datamodel-code-generator`, Zod, `zod-to-json-schema`, OpenTelemetry SDK (Python + JS), Sentry SDK, Grafana Cloud, Google Cloud (Cloud SQL, Memorystore, GKE, Secret Manager, Cloud DNS), Terraform 1.9, GCS remote state, GitHub Actions.

**Source-of-truth specs:**
- `docs/Week-1-2-Foundation-Handoff.md` *(the handoff doc passed via chat — copy it into `docs/handoffs/week-1-2.md` as part of Task 15 if it isn't already there)*
- `CLAUDE.md` (locked tech stack)
- `docs/LockIn_Technical_Roadmap.md` §Phase 1 §1.2 Weeks 1–2

**Decisions locked (Md, 2026-05-11):**
- Cloud: **GCP**.
- OAuth scope for P1: **Google only** (Apple + Microsoft punted to Week 5 polish window).
- Source of truth for event schema: **Zod** (TS native, pydantic generated via JSON Schema bridge).
- Workspace manager: **pnpm**, **Turborepo** (Nx out of scope — smaller blast radius, Vercel-native).

**Authoritative files — do not regenerate:**
- `apps/api/pyproject.toml`, `apps/api/Dockerfile`
- `apps/mcp/pyproject.toml`, `apps/mcp/Dockerfile`
- `CLAUDE.md`, `docs/adr/*.md`

**Working directory convention:** All shell commands assume the repo root `c:\Users\Muzaffar\Desktop\LockIn` unless a step explicitly `cd`s into a subdirectory. The shell is PowerShell 7+ (pwsh). Bash equivalents are noted where syntax diverges.

**Commit cadence:** Commit after each green step group (typically at the end of every numbered task). Conventional Commit prefixes: `feat`, `fix`, `chore`, `docs`, `test`, `ci`, `infra`, `refactor`.

---

## File Structure (what gets created or modified)

### Repo root — new files
- `package.json` — Turborepo root, scripts that fan out to apps
- `pnpm-workspace.yaml` — workspaces: `apps/*`, `packages/*`
- `turbo.json` — pipeline (dev, build, lint, typecheck, test) with caching
- `.nvmrc` — `20.18.0`
- `.npmrc` — pnpm hoisting + strict-peer-dependencies
- `tsconfig.base.json` — strict TS settings inherited by all packages
- `.github/workflows/pr.yml` — PR pipeline
- `.github/workflows/staging.yml` — main → staging
- `.github/workflows/prod.yml` — tag → prod
- `.github/workflows/storybook.yml` — Storybook preview on PR
- `.github/CODEOWNERS`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `scripts/secrets-pull.mjs` — `pnpm secrets:pull` impl (gcloud Secret Manager → `.env.local`)
- `scripts/lint-staged.config.mjs` — Husky/lint-staged glue (optional, if Husky is on)
- `docs/handoffs/week-1-2.md` — handoff note (Task 15)
- `docs/decisions/2026-05-11-cloud-and-oauth.md` — written record of Md's two decisions

### `apps/web/` — modified files (web becomes Turborepo workspace member)
- `apps/web/package.json` — rename from `web` to `@lockin/web`, depend on `@lockin/ui`, `@lockin/events`, `@lockin/shared-types`
- `apps/web/pnpm-workspace.yaml` — **delete** (root workspace replaces it)
- `apps/web/src/app/layout.tsx` — wrap with `SentryErrorBoundary`, RUM init
- `apps/web/sentry.client.config.ts`, `sentry.server.config.ts`, `sentry.edge.config.ts` — new
- `apps/web/src/auth.ts` — NextAuth v5 config (Google + Passkey)
- `apps/web/src/app/api/auth/[...nextauth]/route.ts` — Auth.js route
- `apps/web/src/app/api/webauthn/register/options/route.ts`
- `apps/web/src/app/api/webauthn/register/verify/route.ts`
- `apps/web/src/middleware.ts` — protect `/api/me`, `/dashboard/*`
- `apps/web/tailwind.config.ts` — extend with `@lockin/ui` tokens

### `apps/api/` — modified files
- `apps/api/app/main.py` — wire Sentry + OTel exporter at startup
- `apps/api/app/core/observability.py` — new: OTel + Sentry bootstrap
- `apps/api/app/api/v1/routes/me.py` — `/v1/me` (JWT validation, returns authed user)
- `apps/api/app/api/v1/routes/webauthn.py` — passkey verify endpoint (mirrors web)
- `apps/api/app/core/auth.py` — JWT validator, `Depends(get_current_user)`
- `apps/api/app/events/schemas.py` — **rewrite** to import from `lockin_events` package
- `apps/api/alembic/versions/0001_timescale_events_hypertable.py` — TimescaleDB migration (unapplied)
- `apps/api/pyproject.toml` — **modify** to add `lockin-events` workspace dep + Sentry SDK

### `apps/mcp/` — modified files
- `apps/mcp/app/main.py` — wire Sentry + OTel
- `apps/mcp/app/core/observability.py` — new
- `apps/mcp/pyproject.toml` — add `lockin-events` workspace dep + Sentry SDK

### `packages/events/` — restructured (Zod becomes source of truth)
- `packages/events/package.json` — switch to TS build output, scripts: `build`, `gen:python`, `gen:json-schema`
- `packages/events/tsconfig.json` — emit declarations
- `packages/events/src/schema.ts` — **rewrite** Zod source-of-truth (9 event types)
- `packages/events/src/envelope.ts` — `EventEnvelope`, common fields
- `packages/events/src/streams.ts` — Redis stream name constants
- `packages/events/src/index.ts` — public API
- `packages/events/scripts/emit-json-schema.ts` — Zod → JSON Schema
- `packages/events/scripts/gen-python.sh` — datamodel-code-generator wrapper
- `packages/events/python/pyproject.toml` — make it an installable uv workspace member
- `packages/events/python/lockin_events/__init__.py` — re-exports
- `packages/events/python/lockin_events/envelope.py` — hand-maintained base
- `packages/events/python/lockin_events/generated.py` — codegen output (do not edit by hand)
- `packages/events/python/lockin_events/streams.py` — stream name constants
- `packages/events/dist/json-schema/` — emitted JSON Schemas (committed, regenerated by `pnpm gen:json-schema`)
- `packages/events/fixtures/*.json` — golden-fixtures used by round-trip tests (one per event type)
- `packages/events/tests/schema.test.ts` — TS round-trip + parity check
- `packages/events/python/tests/test_schema_roundtrip.py` — Python round-trip + parity check
- `packages/events/README.md` — versioning rule, regeneration commands

### `packages/shared-types/` — modified
- `packages/shared-types/src/index.ts` — re-export `@lockin/events` + add `ApiError`, `ApiResponse`, `User`

### `packages/ui/` — restructured (becomes a real package)
- `packages/ui/package.json` — switch to TS build output, expose `./tokens.css`, peer-deps React 19, Tailwind v4
- `packages/ui/tsconfig.json` — emit declarations
- `packages/ui/src/index.ts` — public re-exports
- `packages/ui/src/tokens.css` — Tailwind v4 `@theme` tokens
- `packages/ui/src/lib/cn.ts` — `clsx + tailwind-merge` helper
- `packages/ui/src/components/Button.tsx`
- `packages/ui/src/components/Input.tsx`
- `packages/ui/src/components/Card.tsx`
- `packages/ui/src/components/Stack.tsx`
- `packages/ui/src/components/Text.tsx`
- `packages/ui/src/components/Icon.tsx`
- `packages/ui/.storybook/main.ts`
- `packages/ui/.storybook/preview.tsx`
- `packages/ui/src/components/*.stories.tsx` — one per component
- `packages/ui/src/components/*.test.tsx` — Vitest + Testing Library
- `packages/ui/vitest.config.ts`

### `infra/terraform/` — new modules + envs
- `infra/terraform/modules/vpc/main.tf,variables.tf,outputs.tf,versions.tf`
- `infra/terraform/modules/postgres/main.tf,variables.tf,outputs.tf,versions.tf`
- `infra/terraform/modules/redis/main.tf,variables.tf,outputs.tf,versions.tf`
- `infra/terraform/modules/kubernetes/main.tf,variables.tf,outputs.tf,versions.tf`
- `infra/terraform/modules/secrets/main.tf,variables.tf,outputs.tf,versions.tf`
- `infra/terraform/modules/dns/main.tf,variables.tf,outputs.tf,versions.tf`
- `infra/terraform/envs/staging/main.tf,backend.tf,terraform.tfvars.example`
- `infra/terraform/envs/prod/main.tf,backend.tf,terraform.tfvars.example`
- `infra/terraform/README.md` — how to bootstrap state bucket, run plan/apply

### `.gitignore` — append
- `.next/`, `out/`, `dist/`, `*.tsbuildinfo`, `coverage/`, `.turbo/`, `.terraform/`, `*.tfstate*`, `*.tfvars` (allow `.tfvars.example`), `.env.local`, `storybook-static/`

### Files **left untouched**
- `apps/api/pyproject.toml` core (only `[project] dependencies` extended)
- `apps/api/Dockerfile`, `apps/mcp/Dockerfile`
- `bootstrap.ps1` (legacy bootstrap; Turborepo replaces it for app startup but keep for first-time env setup)
- `CLAUDE.md`, `docs/adr/*`

### Files removed
- `apps/web/pnpm-workspace.yaml` (root replaces it)

---

## Task 1 — Root Turborepo + pnpm workspace wiring

**Why first:** Acceptance #1 fails today (`pnpm install && pnpm dev` from root won't boot the three apps). Every later task assumes `pnpm -F <app>` works.

**Files:**
- Create: `package.json`, `pnpm-workspace.yaml`, `turbo.json`, `.nvmrc`, `.npmrc`, `tsconfig.base.json`
- Modify: `apps/web/package.json` (rename to `@lockin/web`), `.gitignore`
- Delete: `apps/web/pnpm-workspace.yaml`

- [ ] **Step 1: Add `.nvmrc` and `.npmrc`**

`.nvmrc`:
```
20.18.0
```

`.npmrc`:
```
strict-peer-dependencies=true
auto-install-peers=true
shamefully-hoist=false
public-hoist-pattern[]=
node-linker=isolated
```

- [ ] **Step 2: Create root `pnpm-workspace.yaml`**

```yaml
packages:
  - "apps/*"
  - "packages/*"
```

- [ ] **Step 3: Create root `tsconfig.base.json`**

```jsonc
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "strict": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true,
    "jsx": "preserve",
    "incremental": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "exclude": ["node_modules", "dist", ".next", ".turbo", "storybook-static"]
}
```

- [ ] **Step 4: Create root `package.json`**

```json
{
  "name": "lockin",
  "version": "0.1.0",
  "private": true,
  "packageManager": "pnpm@9.12.3",
  "scripts": {
    "dev": "turbo run dev --parallel",
    "build": "turbo run build",
    "lint": "turbo run lint",
    "typecheck": "turbo run typecheck",
    "test": "turbo run test",
    "clean": "turbo run clean && rimraf node_modules .turbo",
    "format": "prettier --write \"**/*.{ts,tsx,js,jsx,json,md,yaml,yml}\"",
    "format:check": "prettier --check \"**/*.{ts,tsx,js,jsx,json,md,yaml,yml}\"",
    "events:gen": "pnpm -F @lockin/events run gen",
    "secrets:pull": "node scripts/secrets-pull.mjs",
    "api:dev": "make api",
    "mcp:dev": "make mcp"
  },
  "devDependencies": {
    "turbo": "^2.3.3",
    "prettier": "^3.4.2",
    "rimraf": "^6.0.1",
    "typescript": "^5.7.3"
  },
  "engines": {
    "node": ">=20.18.0",
    "pnpm": ">=9.12.0"
  }
}
```

- [ ] **Step 5: Create root `turbo.json`**

```jsonc
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": [".env", ".env.local", "tsconfig.base.json"],
  "globalEnv": ["NODE_ENV", "CI"],
  "tasks": {
    "dev": {
      "cache": false,
      "persistent": true
    },
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**", "!.next/cache/**"],
      "env": ["NEXT_PUBLIC_*", "SENTRY_*"]
    },
    "lint": {
      "outputs": []
    },
    "typecheck": {
      "dependsOn": ["^build"],
      "outputs": ["*.tsbuildinfo"]
    },
    "test": {
      "dependsOn": ["^build"],
      "outputs": ["coverage/**"]
    },
    "gen": {
      "outputs": ["dist/**", "python/lockin_events/generated.py", "dist/json-schema/**"]
    },
    "clean": {
      "cache": false
    }
  }
}
```

- [ ] **Step 6: Rename `apps/web/package.json` to `@lockin/web` and add scripts**

```json
{
  "name": "@lockin/web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev --port 3000",
    "build": "next build",
    "start": "next start --port 3000",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "clean": "rimraf .next .turbo"
  },
  "dependencies": {
    "@lockin/events": "workspace:*",
    "@lockin/shared-types": "workspace:*",
    "@lockin/ui": "workspace:*",
    "next": "16.2.6",
    "react": "19.2.4",
    "react-dom": "19.2.4"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4",
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "eslint": "^9",
    "eslint-config-next": "16.2.6",
    "rimraf": "^6.0.1",
    "tailwindcss": "^4",
    "typescript": "^5",
    "vitest": "^3.0.5"
  }
}
```

- [ ] **Step 7: Delete `apps/web/pnpm-workspace.yaml`** — root workspace replaces it

```pwsh
Remove-Item apps/web/pnpm-workspace.yaml
```

- [ ] **Step 8: Extend `.gitignore`**

Append:
```
# Turborepo
.turbo/

# Next.js
.next/
out/

# TS incremental
*.tsbuildinfo

# Coverage
coverage/

# Terraform
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
!*.tfvars.example

# Storybook
storybook-static/

# Local env
.env.local
```

- [ ] **Step 9: Install and verify**

```pwsh
pnpm install
pnpm typecheck
pnpm -F @lockin/web dev
```

Expected: `pnpm install` resolves workspace deps; `pnpm typecheck` passes (no source code yet to break); `pnpm -F @lockin/web dev` boots Next on port 3000.

- [ ] **Step 10: Commit**

```pwsh
git add package.json pnpm-workspace.yaml turbo.json .nvmrc .npmrc tsconfig.base.json .gitignore apps/web/package.json
git rm apps/web/pnpm-workspace.yaml
git commit -m "chore(repo): wire Turborepo root + pnpm workspace"
```

---

## Task 2 — Event schema v1 (Zod source-of-truth → TS + Python codegen + round-trip)

**Why next:** Week 3's first concrete write is `task.created`. Until the schema package is round-trippable in both languages, Week 3 cannot start its API+web slice.

**Files:**
- Modify: `packages/events/package.json`, `packages/events/tsconfig.json`
- Create: `packages/events/src/{envelope,schema,streams,index}.ts`
- Create: `packages/events/scripts/{emit-json-schema.ts,gen-python.sh,gen-python.ps1}`
- Create: `packages/events/python/pyproject.toml`, `packages/events/python/lockin_events/{__init__,envelope,streams}.py`
- Create: `packages/events/python/lockin_events/generated.py` (codegen output)
- Create: `packages/events/fixtures/{task.created,task.scheduled,task.accepted,task.rejected,task.modified,task.completed,mood.logged,energy.logged,schedule.explained}.json`
- Create: `packages/events/tests/schema.test.ts`
- Create: `packages/events/python/tests/test_schema_roundtrip.py`
- Create: `packages/events/README.md`
- Modify: `apps/api/app/events/schemas.py` (re-export from `lockin_events`)
- Modify: `apps/api/pyproject.toml` (add `lockin-events` workspace dep)
- Modify: `apps/mcp/pyproject.toml` (add `lockin-events` workspace dep)

- [ ] **Step 1: Replace `packages/events/package.json`**

```json
{
  "name": "@lockin/events",
  "version": "0.1.0",
  "private": true,
  "description": "LockIn event schema — Zod source of truth, TS + Python types generated.",
  "type": "module",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.js"
    },
    "./json-schema/*": "./dist/json-schema/*.json"
  },
  "files": ["dist", "fixtures"],
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "gen:json-schema": "tsx scripts/emit-json-schema.ts",
    "gen:python": "pwsh scripts/gen-python.ps1",
    "gen": "pnpm gen:json-schema && pnpm gen:python && pnpm build",
    "lint": "eslint src",
    "typecheck": "tsc -p tsconfig.json --noEmit",
    "test": "vitest run"
  },
  "dependencies": {
    "zod": "^3.24.1"
  },
  "devDependencies": {
    "@types/node": "^20",
    "tsx": "^4.19.2",
    "typescript": "^5.7.3",
    "vitest": "^3.0.5",
    "zod-to-json-schema": "^3.24.1"
  }
}
```

- [ ] **Step 2: Replace `packages/events/tsconfig.json`**

```jsonc
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "outDir": "dist",
    "rootDir": "src",
    "module": "ESNext",
    "moduleResolution": "Bundler"
  },
  "include": ["src/**/*"]
}
```

- [ ] **Step 3: Write `packages/events/src/envelope.ts`**

```ts
import { z } from "zod";

export const EVENT_VERSION = 1 as const;

export const EventSource = z.enum(["web", "mcp", "api", "agent"]);
export type EventSource = z.infer<typeof EventSource>;

export const eventEnvelope = <T extends z.ZodTypeAny>(payload: T, eventType: string) =>
  z.object({
    event_id: z.string().uuid(),
    event_type: z.literal(eventType),
    event_version: z.literal(EVENT_VERSION),
    user_id: z.string().uuid(),
    tenant_id: z.string().uuid().nullable(),
    occurred_at: z.string().datetime({ offset: true }),
    client_idempotency_key: z.string().min(1).max(128).nullable(),
    source: EventSource,
    payload,
  });

export type EventEnvelope<T> = {
  event_id: string;
  event_type: string;
  event_version: typeof EVENT_VERSION;
  user_id: string;
  tenant_id: string | null;
  occurred_at: string;
  client_idempotency_key: string | null;
  source: EventSource;
  payload: T;
};
```

- [ ] **Step 4: Write `packages/events/src/schema.ts` (all 9 event types)**

```ts
import { z } from "zod";
import { eventEnvelope } from "./envelope.js";

// ---------- Task events ----------

export const TaskCreatedPayload = z.object({
  task_id: z.string().uuid(),
  title: z.string().min(1).max(500),
  source: z.enum(["keyboard", "click", "voice", "mcp"]),
  due_date: z.string().datetime({ offset: true }).optional(),
  priority: z.enum(["low", "medium", "high"]).optional(),
  estimated_minutes: z.number().int().positive().optional(),
});
export const TaskCreatedEvent = eventEnvelope(TaskCreatedPayload, "task.created");

export const TaskScheduledPayload = z.object({
  task_id: z.string().uuid(),
  scheduled_start: z.string().datetime({ offset: true }),
  scheduled_end: z.string().datetime({ offset: true }),
  explanation_id: z.string().uuid(),
});
export const TaskScheduledEvent = eventEnvelope(TaskScheduledPayload, "task.scheduled");

export const TaskAcceptedPayload = z.object({
  task_id: z.string().uuid(),
  schedule_id: z.string().uuid(),
});
export const TaskAcceptedEvent = eventEnvelope(TaskAcceptedPayload, "task.accepted");

export const TaskRejectedPayload = z.object({
  task_id: z.string().uuid(),
  schedule_id: z.string().uuid(),
  reason: z.enum(["wrong_time", "wrong_duration", "wrong_priority", "other"]).optional(),
  free_text: z.string().max(2000).optional(),
});
export const TaskRejectedEvent = eventEnvelope(TaskRejectedPayload, "task.rejected");

export const TaskModifiedPayload = z.object({
  task_id: z.string().uuid(),
  changes: z.record(z.string(), z.unknown()), // additive, free-form; tightened in future versions
});
export const TaskModifiedEvent = eventEnvelope(TaskModifiedPayload, "task.modified");

export const TaskCompletedPayload = z.object({
  task_id: z.string().uuid(),
  completed_at: z.string().datetime({ offset: true }),
  actual_minutes: z.number().int().nonnegative().optional(),
});
export const TaskCompletedEvent = eventEnvelope(TaskCompletedPayload, "task.completed");

// ---------- Signal events (mood + energy) ----------

export const MoodLoggedPayload = z.object({
  mood: z.union([z.literal(1), z.literal(2), z.literal(3), z.literal(4), z.literal(5)]),
  context: z.enum(["morning", "post_lunch", "mid_afternoon", "evening"]).optional(),
});
export const MoodLoggedEvent = eventEnvelope(MoodLoggedPayload, "mood.logged");

export const EnergyLoggedPayload = z.object({
  energy: z.union([z.literal(1), z.literal(2), z.literal(3), z.literal(4), z.literal(5)]),
  context: z.enum(["morning", "post_lunch", "mid_afternoon", "evening"]).optional(),
});
export const EnergyLoggedEvent = eventEnvelope(EnergyLoggedPayload, "energy.logged");

// ---------- Agent events ----------

export const ScheduleExplainedPayload = z.object({
  explanation_id: z.string().uuid(),
  task_id: z.string().uuid(),
  factors: z.array(
    z.object({
      name: z.string(),
      weight: z.number(),
      value: z.union([z.string(), z.number(), z.boolean()]),
    }),
  ),
  model_version: z.string(),
  rendered_text: z.string().max(4000),
});
export const ScheduleExplainedEvent = eventEnvelope(
  ScheduleExplainedPayload,
  "schedule.explained",
);

// ---------- Discriminated union ----------

export const LockInEvent = z.discriminatedUnion("event_type", [
  TaskCreatedEvent,
  TaskScheduledEvent,
  TaskAcceptedEvent,
  TaskRejectedEvent,
  TaskModifiedEvent,
  TaskCompletedEvent,
  MoodLoggedEvent,
  EnergyLoggedEvent,
  ScheduleExplainedEvent,
]);
export type LockInEvent = z.infer<typeof LockInEvent>;

export const EVENT_SCHEMAS = {
  "task.created": TaskCreatedEvent,
  "task.scheduled": TaskScheduledEvent,
  "task.accepted": TaskAcceptedEvent,
  "task.rejected": TaskRejectedEvent,
  "task.modified": TaskModifiedEvent,
  "task.completed": TaskCompletedEvent,
  "mood.logged": MoodLoggedEvent,
  "energy.logged": EnergyLoggedEvent,
  "schedule.explained": ScheduleExplainedEvent,
} as const;
```

- [ ] **Step 5: Write `packages/events/src/streams.ts`**

```ts
export const STREAM_NAMES = {
  TASKS: "events:tasks",
  SIGNALS: "events:signals",
  SCHEDULE: "events:schedule",
  AGENT: "events:agent",
} as const;

export const EVENT_TYPE_TO_STREAM: Record<string, (typeof STREAM_NAMES)[keyof typeof STREAM_NAMES]> = {
  "task.created": STREAM_NAMES.TASKS,
  "task.scheduled": STREAM_NAMES.SCHEDULE,
  "task.accepted": STREAM_NAMES.SCHEDULE,
  "task.rejected": STREAM_NAMES.SCHEDULE,
  "task.modified": STREAM_NAMES.TASKS,
  "task.completed": STREAM_NAMES.TASKS,
  "mood.logged": STREAM_NAMES.SIGNALS,
  "energy.logged": STREAM_NAMES.SIGNALS,
  "schedule.explained": STREAM_NAMES.AGENT,
};
```

- [ ] **Step 6: Write `packages/events/src/index.ts`**

```ts
export * from "./envelope.js";
export * from "./schema.js";
export * from "./streams.js";
```

- [ ] **Step 7: Write `packages/events/scripts/emit-json-schema.ts`**

```ts
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { zodToJsonSchema } from "zod-to-json-schema";
import { EVENT_SCHEMAS } from "../src/schema.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outDir = resolve(__dirname, "../dist/json-schema");
mkdirSync(outDir, { recursive: true });

for (const [eventType, schema] of Object.entries(EVENT_SCHEMAS)) {
  const json = zodToJsonSchema(schema, { name: eventType, $refStrategy: "none" });
  const fileName = eventType.replace(/\./g, "_") + ".json";
  writeFileSync(resolve(outDir, fileName), JSON.stringify(json, null, 2));
  // eslint-disable-next-line no-console
  console.log(`wrote ${fileName}`);
}
```

- [ ] **Step 8: Write `packages/events/scripts/gen-python.ps1`** (PowerShell because the dev env is Windows)

```powershell
#!/usr/bin/env pwsh
# Regenerate lockin_events.generated from emitted JSON Schemas.
$ErrorActionPreference = "Stop"

$pkgRoot   = Resolve-Path "$PSScriptRoot/.."
$schemaDir = Join-Path $pkgRoot "dist/json-schema"
$outFile   = Join-Path $pkgRoot "python/lockin_events/generated.py"

if (-not (Test-Path $schemaDir)) {
    throw "JSON schemas not found at $schemaDir. Run 'pnpm gen:json-schema' first."
}

# Use uvx so we don't pollute the host. datamodel-code-generator picks one file at a time;
# concatenate by passing the schema directory as input.
uvx --from "datamodel-code-generator>=0.26" datamodel-codegen `
    --input $schemaDir `
    --input-file-type jsonschema `
    --output $outFile `
    --output-model-type pydantic_v2.BaseModel `
    --target-python-version 3.12 `
    --use-double-quotes `
    --disable-timestamp `
    --use-schema-description

Write-Host "Generated $outFile"
```

A POSIX twin at `packages/events/scripts/gen-python.sh` mirrors the same `uvx datamodel-codegen ...` command for non-Windows runners. CI runs on Ubuntu, so both must exist.

- [ ] **Step 9: Write `packages/events/python/pyproject.toml`** (so uv can install it as a workspace dep)

```toml
[project]
name = "lockin-events"
version = "0.1.0"
description = "LockIn event schema (Python) — generated from packages/events/src/schema.ts"
requires-python = ">=3.12"
readme = "../README.md"
license = { text = "Proprietary" }
dependencies = ["pydantic>=2.9"]

[tool.uv]
package = true

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["lockin_events"]
```

- [ ] **Step 10: Write `packages/events/python/lockin_events/envelope.py`** (hand-maintained)

```python
"""Event envelope shared by every LockIn event type.

Source of truth: packages/events/src/envelope.ts. Regenerate generated.py
via `pnpm gen:python` after any schema change.
"""

from __future__ import annotations

from typing import Literal

EVENT_VERSION: Literal[1] = 1
EventSource = Literal["web", "mcp", "api", "agent"]
```

- [ ] **Step 11: Write `packages/events/python/lockin_events/streams.py`**

```python
from typing import Final

STREAM_TASKS: Final[str] = "events:tasks"
STREAM_SIGNALS: Final[str] = "events:signals"
STREAM_SCHEDULE: Final[str] = "events:schedule"
STREAM_AGENT: Final[str] = "events:agent"

EVENT_TYPE_TO_STREAM: Final[dict[str, str]] = {
    "task.created": STREAM_TASKS,
    "task.scheduled": STREAM_SCHEDULE,
    "task.accepted": STREAM_SCHEDULE,
    "task.rejected": STREAM_SCHEDULE,
    "task.modified": STREAM_TASKS,
    "task.completed": STREAM_TASKS,
    "mood.logged": STREAM_SIGNALS,
    "energy.logged": STREAM_SIGNALS,
    "schedule.explained": STREAM_AGENT,
}
```

- [ ] **Step 12: Write `packages/events/python/lockin_events/__init__.py`**

```python
from lockin_events.envelope import EVENT_VERSION, EventSource
from lockin_events.streams import (
    EVENT_TYPE_TO_STREAM,
    STREAM_AGENT,
    STREAM_SCHEDULE,
    STREAM_SIGNALS,
    STREAM_TASKS,
)

# generated.py is overwritten by `pnpm gen:python`. Import lazily so an
# unbuilt clone still gives a helpful error rather than a NameError.
try:
    from lockin_events.generated import *  # noqa: F401,F403
except ImportError as exc:  # pragma: no cover - dev-time guidance
    raise ImportError(
        "lockin_events.generated is missing. Run `pnpm -F @lockin/events gen` "
        "to produce it from packages/events/src/schema.ts."
    ) from exc

__all__ = [
    "EVENT_TYPE_TO_STREAM",
    "EVENT_VERSION",
    "EventSource",
    "STREAM_AGENT",
    "STREAM_SCHEDULE",
    "STREAM_SIGNALS",
    "STREAM_TASKS",
]
```

- [ ] **Step 13: Write fixtures (one per event type) under `packages/events/fixtures/`**

Each fixture is a minimal-but-complete valid event. Example `task.created.json`:

```json
{
  "event_id": "01927a45-3d80-7c10-8a7e-3a9b1c2d4e5f",
  "event_type": "task.created",
  "event_version": 1,
  "user_id": "11111111-1111-4111-8111-111111111111",
  "tenant_id": null,
  "occurred_at": "2026-05-11T10:30:00+00:00",
  "client_idempotency_key": "task-create-abc-123",
  "source": "web",
  "payload": {
    "task_id": "22222222-2222-4222-8222-222222222222",
    "title": "Finish foundation slice",
    "source": "keyboard"
  }
}
```

Write one fixture per event type (9 total). Use real UUIDs (any v4 will do) and a stable `occurred_at`.

- [ ] **Step 14: Write `packages/events/tests/schema.test.ts` (Vitest round-trip)**

```ts
import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, test } from "vitest";
import { EVENT_SCHEMAS, LockInEvent } from "../src/index.js";

const fixturesDir = resolve(__dirname, "../fixtures");

describe("event schema fixtures", () => {
  const files = readdirSync(fixturesDir).filter((f) => f.endsWith(".json"));

  test("there is a fixture for every event type", () => {
    expect(new Set(files.map((f) => f.replace(/\.json$/, "")))).toEqual(
      new Set(Object.keys(EVENT_SCHEMAS)),
    );
  });

  for (const file of files) {
    const eventType = file.replace(/\.json$/, "") as keyof typeof EVENT_SCHEMAS;
    test(`${eventType} round-trips through Zod`, () => {
      const raw = JSON.parse(readFileSync(resolve(fixturesDir, file), "utf-8"));
      const parsed = EVENT_SCHEMAS[eventType].parse(raw);
      // serialize, reparse, compare
      const reparsed = EVENT_SCHEMAS[eventType].parse(JSON.parse(JSON.stringify(parsed)));
      expect(reparsed).toEqual(parsed);
    });

    test(`${eventType} parses through the discriminated union`, () => {
      const raw = JSON.parse(readFileSync(resolve(fixturesDir, file), "utf-8"));
      const parsed = LockInEvent.parse(raw);
      expect(parsed.event_type).toBe(eventType);
    });
  }
});
```

- [ ] **Step 15: Write `packages/events/python/tests/test_schema_roundtrip.py`**

```python
"""Round-trip every fixture through the generated pydantic models.

Source of truth: packages/events/src/schema.ts. If this test fails after a
schema change, you forgot to run `pnpm -F @lockin/events gen`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from lockin_events import generated as gen

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures"

EVENT_TYPE_TO_MODEL = {
    "task.created": gen.TaskCreated,
    "task.scheduled": gen.TaskScheduled,
    "task.accepted": gen.TaskAccepted,
    "task.rejected": gen.TaskRejected,
    "task.modified": gen.TaskModified,
    "task.completed": gen.TaskCompleted,
    "mood.logged": gen.MoodLogged,
    "energy.logged": gen.EnergyLogged,
    "schedule.explained": gen.ScheduleExplained,
}


@pytest.mark.parametrize("fixture_path", sorted(FIXTURE_DIR.glob("*.json")))
def test_fixture_roundtrips(fixture_path: Path) -> None:
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    model_cls = EVENT_TYPE_TO_MODEL[raw["event_type"]]
    obj = model_cls.model_validate(raw)
    reserialized = obj.model_dump(mode="json", exclude_none=False)
    reparsed = model_cls.model_validate(reserialized)
    assert reparsed == obj


def test_every_event_type_has_a_model() -> None:
    expected = set(EVENT_TYPE_TO_MODEL.keys())
    actual = {p.stem.replace("_", ".") for p in FIXTURE_DIR.glob("*.json")}
    assert expected == actual
```

> **Note on generated class names:** `datamodel-code-generator` names classes after the JSON Schema `title`. The `name` arg passed to `zodToJsonSchema` in Step 7 is `"task.created"` — datamodel-code-generator will sanitize this to `TaskCreated`. If the actual generated names differ, update the `EVENT_TYPE_TO_MODEL` map. The first run is the moment to verify by reading `generated.py`.

- [ ] **Step 16: Write `packages/events/README.md`**

```markdown
# @lockin/events

Source of truth for the LockIn event schema.

## Source of truth
- `src/schema.ts` (Zod) is the **only** place to add or modify events.
- `dist/json-schema/*.json` (emitted) and `python/lockin_events/generated.py` (codegen) are derived artifacts. Do not edit by hand.

## Regenerate after any schema change
```bash
pnpm -F @lockin/events gen
```
This runs three steps: emit JSON Schema, run `datamodel-code-generator` into `python/lockin_events/generated.py`, then `tsc -b` for the TS output.

## Versioning rule
- Additive optional fields → no version bump.
- Removal, rename, or semantic change → bump `event_version` and document a migration path.
- Breaking changes require Md sign-off (the behavior graph forks otherwise).

## Streams
`events:tasks`, `events:signals`, `events:schedule`, `events:agent`. See `streams.ts` / `streams.py`.
```

- [ ] **Step 17: Update `apps/api/pyproject.toml` to depend on the workspace package**

In `[project] dependencies`, append:
```toml
"lockin-events",
```

In `[tool.uv.sources]`, replace the commented stub with:
```toml
lockin-events = { workspace = true }
```

In root or `apps/api`, ensure `tool.uv.workspace.members = ["../../packages/events/python"]` is recognized. The simplest path: create `pyproject.toml` at the repo root with a minimal `[tool.uv.workspace]` block listing every Python member:

```toml
[tool.uv.workspace]
members = ["apps/api", "apps/mcp", "packages/events/python"]
```

(This root `pyproject.toml` is **only** for uv workspace discovery — it has no `[project]` table.)

- [ ] **Step 18: Rewrite `apps/api/app/events/schemas.py` to thin re-export**

```python
"""Re-export the canonical event schemas.

Canonical source: packages/events/src/schema.ts (Zod). Generated pydantic models
live in `lockin_events.generated`. Do not redefine event types here.
"""

from lockin_events import *  # noqa: F401,F403
from lockin_events.envelope import EVENT_VERSION, EventSource  # noqa: F401
from lockin_events.streams import EVENT_TYPE_TO_STREAM  # noqa: F401
```

- [ ] **Step 19: Mirror the workspace dep in `apps/mcp/pyproject.toml`**

Same change as Step 17, in `apps/mcp/pyproject.toml`.

- [ ] **Step 20: Generate, install, and run all tests**

```pwsh
pnpm install
pnpm -F @lockin/events gen
pnpm -F @lockin/events test
# Sync the uv workspaces so apps/api and apps/mcp see lockin-events
uv sync --workspace
uv run --directory packages/events/python python -m pytest
uv run --directory apps/api python -m pytest
```

Expected: TS tests pass (9 round-trips + union parity + fixture coverage). Python tests pass (9 round-trips + parity). `apps/api` tests still pass (health smoke).

- [ ] **Step 21: Commit**

```pwsh
git add packages/events packages/shared-types apps/api/app/events/schemas.py apps/api/pyproject.toml apps/mcp/pyproject.toml pyproject.toml
git commit -m "feat(events): v1 schema — Zod source-of-truth, TS + Python round-trip"
```

---

## Task 3 — `packages/ui` base components + Tailwind tokens

**Why:** Acceptance #7 — `apps/web` imports `Button` from `@lockin/ui`. Also unblocks Week 3 (task-capture input UI needs `Input`, `Button`, `Stack`, `Text`).

**Files:**
- Modify: `packages/ui/package.json`, `packages/ui/tsconfig.json`
- Create: `packages/ui/src/tokens.css`
- Create: `packages/ui/src/lib/cn.ts`
- Create: `packages/ui/src/components/{Button,Input,Card,Stack,Text,Icon}.tsx`
- Create: `packages/ui/src/components/{Button,Input,Card,Stack,Text,Icon}.test.tsx`
- Create: `packages/ui/vitest.config.ts`
- Modify: `apps/web/tailwind.config.ts` (extend with token references)
- Modify: `apps/web/src/app/page.tsx` to render `<Button>` (proves the import path)

- [ ] **Step 1: Replace `packages/ui/package.json`**

```json
{
  "name": "@lockin/ui",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.js"
    },
    "./tokens.css": "./src/tokens.css"
  },
  "files": ["dist", "src/tokens.css"],
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "lint": "eslint src",
    "typecheck": "tsc -p tsconfig.json --noEmit",
    "test": "vitest run"
  },
  "peerDependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "dependencies": {
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.6.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.1.0",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "@vitejs/plugin-react": "^4.3.4",
    "jsdom": "^25.0.1",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "typescript": "^5.7.3",
    "vitest": "^3.0.5"
  }
}
```

- [ ] **Step 2: Replace `packages/ui/tsconfig.json`**

```jsonc
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "outDir": "dist",
    "rootDir": "src",
    "jsx": "react-jsx",
    "module": "ESNext",
    "moduleResolution": "Bundler"
  },
  "include": ["src/**/*"],
  "exclude": ["**/*.test.tsx", "**/*.test.ts", "**/*.stories.tsx"]
}
```

- [ ] **Step 3: Write `packages/ui/src/tokens.css` (Tailwind v4 `@theme`)**

```css
/* LockIn design tokens — Tailwind v4 @theme block.
 * Consumed by apps/web via `@import "@lockin/ui/tokens.css";`.
 * Dark mode variants are scaffolded; refinement is a P2 task. */

@theme {
  /* Brand */
  --color-brand-50:  oklch(0.97 0.02 270);
  --color-brand-500: oklch(0.62 0.18 270);
  --color-brand-900: oklch(0.25 0.10 270);

  /* Semantic surfaces */
  --color-surface:        oklch(0.99 0.00 0);
  --color-surface-muted:  oklch(0.96 0.00 0);
  --color-text:           oklch(0.15 0.00 0);
  --color-text-muted:     oklch(0.45 0.00 0);
  --color-border:         oklch(0.90 0.00 0);
  --color-danger:         oklch(0.55 0.20 25);
  --color-success:        oklch(0.60 0.16 145);

  /* Type scale */
  --font-sans: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, "Cascadia Mono", monospace;
  --text-xs:   0.75rem;
  --text-sm:   0.875rem;
  --text-base: 1rem;
  --text-lg:   1.125rem;
  --text-xl:   1.25rem;
  --text-2xl:  1.5rem;
  --text-3xl:  1.875rem;

  /* Spacing scale (4px base) */
  --spacing-0: 0;
  --spacing-1: 0.25rem;
  --spacing-2: 0.5rem;
  --spacing-3: 0.75rem;
  --spacing-4: 1rem;
  --spacing-6: 1.5rem;
  --spacing-8: 2rem;
  --spacing-12: 3rem;

  /* Motion */
  --duration-fast:   120ms;
  --duration-medium: 200ms;
  --duration-slow:   320ms;
  --ease-out:    cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);

  /* Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-pill: 9999px;
}

@media (prefers-color-scheme: dark) {
  @theme {
    --color-surface:        oklch(0.16 0.00 0);
    --color-surface-muted:  oklch(0.22 0.00 0);
    --color-text:           oklch(0.96 0.00 0);
    --color-text-muted:     oklch(0.70 0.00 0);
    --color-border:         oklch(0.30 0.00 0);
  }
}
```

- [ ] **Step 4: Write `packages/ui/src/lib/cn.ts`**

```ts
import clsx, { type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const cn = (...inputs: ClassValue[]): string => twMerge(clsx(inputs));
```

- [ ] **Step 5: Write `packages/ui/src/components/Button.tsx`**

```tsx
import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "../lib/cn.js";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

const VARIANT_CLASSES: Record<Variant, string> = {
  primary: "bg-brand-500 text-white hover:bg-brand-900 focus-visible:ring-brand-500",
  secondary: "bg-surface-muted text-text hover:bg-border focus-visible:ring-brand-500",
  ghost: "bg-transparent text-text hover:bg-surface-muted focus-visible:ring-brand-500",
  danger: "bg-danger text-white hover:opacity-90 focus-visible:ring-danger",
};

const SIZE_CLASSES: Record<Size, string> = {
  sm: "h-8 px-3 text-sm rounded-md",
  md: "h-10 px-4 text-base rounded-md",
  lg: "h-12 px-6 text-lg rounded-lg",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = "primary", size = "md", type = "button", ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={cn(
        "inline-flex items-center justify-center gap-2 font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        "disabled:opacity-50 disabled:pointer-events-none",
        VARIANT_CLASSES[variant],
        SIZE_CLASSES[size],
        className,
      )}
      {...rest}
    />
  );
});
```

- [ ] **Step 6: Write `packages/ui/src/components/Input.tsx`**

```tsx
import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "../lib/cn.js";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, invalid, ...rest },
  ref,
) {
  return (
    <input
      ref={ref}
      aria-invalid={invalid || undefined}
      className={cn(
        "block w-full h-10 px-3 text-base rounded-md border bg-surface text-text",
        "placeholder:text-text-muted",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2",
        invalid ? "border-danger" : "border-border",
        className,
      )}
      {...rest}
    />
  );
});
```

- [ ] **Step 7: Write `packages/ui/src/components/Card.tsx`**

```tsx
import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "../lib/cn.js";

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  function Card({ className, ...rest }, ref) {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-lg border border-border bg-surface p-6 shadow-sm",
          className,
        )}
        {...rest}
      />
    );
  },
);
```

- [ ] **Step 8: Write `packages/ui/src/components/Stack.tsx`**

```tsx
import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "../lib/cn.js";

export interface StackProps extends HTMLAttributes<HTMLDivElement> {
  direction?: "row" | "col";
  gap?: 1 | 2 | 3 | 4 | 6 | 8 | 12;
  align?: "start" | "center" | "end" | "stretch";
  justify?: "start" | "center" | "end" | "between";
}

const GAP: Record<NonNullable<StackProps["gap"]>, string> = {
  1: "gap-1", 2: "gap-2", 3: "gap-3", 4: "gap-4", 6: "gap-6", 8: "gap-8", 12: "gap-12",
};

export const Stack = forwardRef<HTMLDivElement, StackProps>(function Stack(
  { className, direction = "col", gap = 4, align, justify, ...rest },
  ref,
) {
  return (
    <div
      ref={ref}
      className={cn(
        "flex",
        direction === "row" ? "flex-row" : "flex-col",
        GAP[gap],
        align && `items-${align}`,
        justify && `justify-${justify}`,
        className,
      )}
      {...rest}
    />
  );
});
```

- [ ] **Step 9: Write `packages/ui/src/components/Text.tsx`**

```tsx
import { forwardRef, type HTMLAttributes, type ElementType } from "react";
import { cn } from "../lib/cn.js";

type Size = "xs" | "sm" | "base" | "lg" | "xl" | "2xl" | "3xl";
type Tone = "default" | "muted" | "danger" | "success";

export interface TextProps extends HTMLAttributes<HTMLElement> {
  as?: ElementType;
  size?: Size;
  tone?: Tone;
  weight?: "normal" | "medium" | "semibold" | "bold";
}

const SIZE: Record<Size, string> = {
  xs: "text-xs", sm: "text-sm", base: "text-base", lg: "text-lg",
  xl: "text-xl", "2xl": "text-2xl", "3xl": "text-3xl",
};

const TONE: Record<Tone, string> = {
  default: "text-text",
  muted: "text-text-muted",
  danger: "text-danger",
  success: "text-success",
};

export const Text = forwardRef<HTMLElement, TextProps>(function Text(
  { as: Component = "p", className, size = "base", tone = "default", weight, ...rest },
  ref,
) {
  return (
    <Component
      ref={ref as never}
      className={cn(SIZE[size], TONE[tone], weight && `font-${weight}`, className)}
      {...rest}
    />
  );
});
```

- [ ] **Step 10: Write `packages/ui/src/components/Icon.tsx`**

```tsx
import { forwardRef, type SVGAttributes, type ReactNode } from "react";
import { cn } from "../lib/cn.js";

export interface IconProps extends SVGAttributes<SVGSVGElement> {
  label?: string; // accessible name; omit to mark as decorative
  size?: 16 | 20 | 24 | 32;
  children: ReactNode; // SVG content (paths, etc.)
}

export const Icon = forwardRef<SVGSVGElement, IconProps>(function Icon(
  { label, size = 20, className, children, ...rest },
  ref,
) {
  const decorative = !label;
  return (
    <svg
      ref={ref}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={decorative || undefined}
      aria-label={label}
      role={decorative ? undefined : "img"}
      className={cn("inline-block shrink-0", className)}
      {...rest}
    >
      {children}
    </svg>
  );
});
```

- [ ] **Step 11: Write `packages/ui/src/index.ts`**

```ts
export { Button, type ButtonProps } from "./components/Button.js";
export { Input, type InputProps } from "./components/Input.js";
export { Card } from "./components/Card.js";
export { Stack, type StackProps } from "./components/Stack.js";
export { Text, type TextProps } from "./components/Text.js";
export { Icon, type IconProps } from "./components/Icon.js";
export { cn } from "./lib/cn.js";
```

- [ ] **Step 12: Write `packages/ui/vitest.config.ts`**

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
  },
});
```

And `packages/ui/vitest.setup.ts`:
```ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 13: Write tests for each component**

Example `Button.test.tsx`:
```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import { Button } from "./Button.js";

describe("Button", () => {
  test("renders with default variant", () => {
    render(<Button>Submit</Button>);
    const btn = screen.getByRole("button", { name: "Submit" });
    expect(btn).toBeInTheDocument();
    expect(btn).toHaveAttribute("type", "button");
  });

  test("respects type override", () => {
    render(<Button type="submit">Go</Button>);
    expect(screen.getByRole("button")).toHaveAttribute("type", "submit");
  });

  test("disabled state blocks pointer", () => {
    render(<Button disabled>Off</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
```

Mirror the pattern for `Input` (invalid state sets `aria-invalid`), `Stack` (renders flex-direction class), `Text` (renders chosen element via `as`), `Icon` (decorative gets `aria-hidden`, labeled gets `role="img"`), `Card` (renders children inside a div with the expected class).

- [ ] **Step 14: Wire `apps/web` to consume `@lockin/ui`**

Modify `apps/web/src/app/globals.css` (first line):
```css
@import "@lockin/ui/tokens.css";
@import "tailwindcss";
```

Modify `apps/web/src/app/page.tsx` to render a `<Button>`:
```tsx
import { Button, Stack, Text } from "@lockin/ui";

export default function Home() {
  return (
    <main className="min-h-dvh grid place-items-center bg-surface text-text">
      <Stack gap={4} align="center">
        <Text as="h1" size="3xl" weight="bold">LockIn</Text>
        <Text tone="muted">Foundation slice — design system smoke test.</Text>
        <Button variant="primary">Press Cmd+K (Week 3)</Button>
      </Stack>
    </main>
  );
}
```

- [ ] **Step 15: Build, install, test**

```pwsh
pnpm install
pnpm -F @lockin/ui build
pnpm -F @lockin/ui test
pnpm -F @lockin/web build
```

Expected: ui build emits `dist/index.{js,d.ts}` and per-component artifacts; ui tests pass (≥6 component test files); web build succeeds with the new imports.

- [ ] **Step 16: Lighthouse check (manual, acceptance gate)**

```pwsh
pnpm -F @lockin/web start
# In another shell:
pnpm dlx @lhci/cli@0.14.x autorun --collect.url=http://localhost:3000 --upload.target=temporary-public-storage
```

Expected: scores ≥95 on every axis. If perf <95, investigate font loading and remove any inline `<img>`s without `width`/`height`.

- [ ] **Step 17: Commit**

```pwsh
git add packages/ui apps/web/src/app/globals.css apps/web/src/app/page.tsx apps/web/package.json
git commit -m "feat(ui): base design-system components + Tailwind v4 tokens"
```

---

## Task 4 — Storybook for `packages/ui` + preview deploy

**Why:** Acceptance #7 — Storybook preview deploys on PR.

**Files:**
- Create: `packages/ui/.storybook/{main.ts,preview.tsx}`
- Create: `packages/ui/src/components/*.stories.tsx` (6 files)
- Create: `.github/workflows/storybook.yml`
- Modify: `packages/ui/package.json` (add `storybook`, `build-storybook` scripts and deps)

- [ ] **Step 1: Add Storybook scripts + deps to `packages/ui/package.json`**

In `scripts`:
```json
"storybook": "storybook dev -p 6006",
"build-storybook": "storybook build --output-dir storybook-static"
```

In `devDependencies`:
```json
"@storybook/addon-essentials": "^8.4.7",
"@storybook/react": "^8.4.7",
"@storybook/react-vite": "^8.4.7",
"storybook": "^8.4.7"
```

- [ ] **Step 2: `packages/ui/.storybook/main.ts`**

```ts
import type { StorybookConfig } from "@storybook/react-vite";

const config: StorybookConfig = {
  stories: ["../src/**/*.stories.@(ts|tsx)"],
  addons: ["@storybook/addon-essentials"],
  framework: { name: "@storybook/react-vite", options: {} },
  typescript: { reactDocgen: "react-docgen-typescript" },
};

export default config;
```

- [ ] **Step 3: `packages/ui/.storybook/preview.tsx`**

```tsx
import type { Preview } from "@storybook/react";
import "../src/tokens.css";
import "./tailwind.css";

const preview: Preview = {
  parameters: {
    controls: { matchers: { color: /(background|color)$/i, date: /Date$/i } },
    backgrounds: {
      default: "surface",
      values: [
        { name: "surface", value: "var(--color-surface)" },
        { name: "muted", value: "var(--color-surface-muted)" },
      ],
    },
  },
};

export default preview;
```

`packages/ui/.storybook/tailwind.css`:
```css
@import "tailwindcss";
@source "../src/**/*.{ts,tsx}";
```

- [ ] **Step 4: Write a story per component**

Example `Button.stories.tsx`:
```tsx
import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./Button.js";

const meta = {
  title: "Components/Button",
  component: Button,
  args: { children: "Press me" },
  argTypes: {
    variant: { control: "radio", options: ["primary", "secondary", "ghost", "danger"] },
    size: { control: "radio", options: ["sm", "md", "lg"] },
  },
} satisfies Meta<typeof Button>;
export default meta;

export const Primary: StoryObj<typeof meta> = { args: { variant: "primary" } };
export const Secondary: StoryObj<typeof meta> = { args: { variant: "secondary" } };
export const Ghost: StoryObj<typeof meta> = { args: { variant: "ghost" } };
export const Danger: StoryObj<typeof meta> = { args: { variant: "danger" } };
export const Sizes: StoryObj<typeof meta> = {
  render: (args) => (
    <div className="flex gap-3 items-center">
      <Button {...args} size="sm">Small</Button>
      <Button {...args} size="md">Medium</Button>
      <Button {...args} size="lg">Large</Button>
    </div>
  ),
};
```

Mirror for `Input`, `Card`, `Stack`, `Text`, `Icon`.

- [ ] **Step 5: `.github/workflows/storybook.yml`** (deploys static build as a Vercel preview)

```yaml
name: storybook
on:
  pull_request:
    paths:
      - "packages/ui/**"
      - ".github/workflows/storybook.yml"

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9.12.3 }
      - uses: actions/setup-node@v4
        with:
          node-version-file: ".nvmrc"
          cache: "pnpm"
      - run: pnpm install --frozen-lockfile
      - run: pnpm -F @lockin/events gen
      - run: pnpm -F @lockin/ui build-storybook
      - name: Deploy preview to Vercel
        id: deploy
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_STORYBOOK_PROJECT_ID }}
          working-directory: packages/ui/storybook-static
      - uses: actions/github-script@v7
        with:
          script: |
            const url = "${{ steps.deploy.outputs.preview-url }}";
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `📚 Storybook preview: ${url}`
            });
```

- [ ] **Step 6: Run locally and commit**

```pwsh
pnpm install
pnpm -F @lockin/ui storybook  # smoke test, then Ctrl+C
pnpm -F @lockin/ui build-storybook
git add packages/ui/.storybook packages/ui/src/components/*.stories.tsx .github/workflows/storybook.yml packages/ui/package.json
git commit -m "ci(ui): Storybook preview deploy on PR"
```

---

## Task 5 — GitHub Actions CI: PR pipeline

**Why:** Acceptance #2 — PR pipeline runs only changed-package tests and stays green.

**Files:**
- Create: `.github/workflows/pr.yml`
- Create: `.github/CODEOWNERS`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`

- [ ] **Step 1: `.github/workflows/pr.yml`**

```yaml
name: pr
on:
  pull_request:
    branches: [main]
  workflow_dispatch:

concurrency:
  group: pr-${{ github.ref }}
  cancel-in-progress: true

jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      web: ${{ steps.changes.outputs.web }}
      api: ${{ steps.changes.outputs.api }}
      mcp: ${{ steps.changes.outputs.mcp }}
      packages: ${{ steps.changes.outputs.packages }}
      infra: ${{ steps.changes.outputs.infra }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: changes
        with:
          filters: |
            web:
              - 'apps/web/**'
              - 'packages/**'
              - 'pnpm-lock.yaml'
              - 'turbo.json'
              - 'tsconfig.base.json'
            api:
              - 'apps/api/**'
              - 'packages/events/**'
            mcp:
              - 'apps/mcp/**'
              - 'packages/events/**'
            packages:
              - 'packages/**'
            infra:
              - 'infra/terraform/**'

  js:
    needs: detect
    if: needs.detect.outputs.web == 'true' || needs.detect.outputs.packages == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9.12.3 }
      - uses: actions/setup-node@v4
        with:
          node-version-file: ".nvmrc"
          cache: "pnpm"
      - run: pnpm install --frozen-lockfile
      - run: pnpm -F @lockin/events gen
      - run: pnpm lint
      - run: pnpm typecheck
      - run: pnpm test
      - run: pnpm build

  python-api:
    needs: detect
    if: needs.detect.outputs.api == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9.12.3 }
      - uses: actions/setup-node@v4
        with:
          node-version-file: ".nvmrc"
          cache: "pnpm"
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - uses: astral-sh/setup-uv@v3
        with: { version: "0.5.x" }
      - run: pnpm install --frozen-lockfile
      - run: pnpm -F @lockin/events gen
      - run: uv sync --workspace
      - run: uv run --directory apps/api python -m ruff check .
      - run: uv run --directory apps/api python -m mypy app
      - run: uv run --directory apps/api python -m pytest

  python-mcp:
    needs: detect
    if: needs.detect.outputs.mcp == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9.12.3 }
      - uses: actions/setup-node@v4
        with:
          node-version-file: ".nvmrc"
          cache: "pnpm"
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - uses: astral-sh/setup-uv@v3
        with: { version: "0.5.x" }
      - run: pnpm install --frozen-lockfile
      - run: pnpm -F @lockin/events gen
      - run: uv sync --workspace
      - run: uv run --directory apps/mcp python -m ruff check .
      - run: uv run --directory apps/mcp python -m mypy app
      - run: uv run --directory apps/mcp python -m pytest

  terraform-plan:
    needs: detect
    if: needs.detect.outputs.infra == 'true'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write  # for OIDC to GCP later
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with: { terraform_version: "1.9.8" }
      - name: tf fmt
        run: terraform -chdir=infra/terraform fmt -check -recursive
      - name: tf validate (staging)
        run: |
          terraform -chdir=infra/terraform/envs/staging init -backend=false
          terraform -chdir=infra/terraform/envs/staging validate

  gate:
    needs: [js, python-api, python-mcp, terraform-plan]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: All required checks passed
        run: |
          for r in "${{ needs.js.result }}" "${{ needs.python-api.result }}" "${{ needs.python-mcp.result }}" "${{ needs.terraform-plan.result }}"; do
            if [ "$r" = "failure" ] || [ "$r" = "cancelled" ]; then
              echo "Required job failed: $r"; exit 1
            fi
          done
```

- [ ] **Step 2: `.github/CODEOWNERS`**

```
*           @Muzaffar-codes07
/infra/     @Muzaffar-codes07
/apps/api/  @Muzaffar-codes07
/apps/mcp/  @Muzaffar-codes07
/apps/web/  @Muzaffar-codes07
/packages/  @Muzaffar-codes07
```

- [ ] **Step 3: `.github/PULL_REQUEST_TEMPLATE.md`**

```markdown
## Summary
-

## Slice
> Which slice in `docs/CURRENT_SLICE.md` does this advance?

## Checks
- [ ] Lint, typecheck, tests pass locally
- [ ] No new dependencies introduced without an ADR
- [ ] No secrets in diff (grep)
- [ ] If schema changed: `pnpm -F @lockin/events gen` was re-run
- [ ] If infra changed: `terraform plan` output reviewed in CI
```

- [ ] **Step 4: Commit**

```pwsh
git add .github
git commit -m "ci: PR pipeline with changed-package detection"
```

---

## Task 6 — GitHub Actions CI: main → staging + tag → prod

**Why:** Acceptance #2 — merge to main deploys staging in <8 min; tag → prod with manual approval.

**Files:**
- Create: `.github/workflows/staging.yml`
- Create: `.github/workflows/prod.yml`

- [ ] **Step 1: `.github/workflows/staging.yml`**

```yaml
name: staging
on:
  push:
    branches: [main]
  workflow_dispatch:

concurrency:
  group: staging
  cancel-in-progress: false

permissions:
  contents: read
  id-token: write  # OIDC to GCP

jobs:
  web:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9.12.3 }
      - uses: actions/setup-node@v4
        with:
          node-version-file: ".nvmrc"
          cache: "pnpm"
      - run: pnpm install --frozen-lockfile
      - run: pnpm -F @lockin/events gen
      - run: pnpm -F @lockin/web build
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_WEB_PROJECT_ID }}
          working-directory: apps/web
          vercel-args: "--prod=false"

  api:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_DEPLOY_SA }}
      - uses: google-github-actions/setup-gcloud@v2
      - run: gcloud auth configure-docker us-central1-docker.pkg.dev
      - name: Build and push image
        run: |
          IMAGE="us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/lockin/api:${{ github.sha }}"
          docker build -f apps/api/Dockerfile -t "$IMAGE" .
          docker push "$IMAGE"
      - uses: google-github-actions/get-gke-credentials@v2
        with:
          cluster_name: lockin-staging
          location: us-central1
      - name: Roll deployment
        run: |
          kubectl set image deploy/api api="us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/lockin/api:${{ github.sha }}" -n lockin
          kubectl rollout status deploy/api -n lockin --timeout=300s

  mcp:
    runs-on: ubuntu-latest
    environment: staging
    needs: api
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_DEPLOY_SA }}
      - uses: google-github-actions/setup-gcloud@v2
      - run: gcloud auth configure-docker us-central1-docker.pkg.dev
      - name: Build and push image
        run: |
          IMAGE="us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/lockin/mcp:${{ github.sha }}"
          docker build -f apps/mcp/Dockerfile -t "$IMAGE" .
          docker push "$IMAGE"
      - uses: google-github-actions/get-gke-credentials@v2
        with:
          cluster_name: lockin-staging
          location: us-central1
      - name: Roll deployment
        run: |
          kubectl set image deploy/mcp mcp="us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/lockin/mcp:${{ github.sha }}" -n lockin
          kubectl rollout status deploy/mcp -n lockin --timeout=300s
```

- [ ] **Step 2: `.github/workflows/prod.yml`**

```yaml
name: prod
on:
  push:
    tags: ["v*.*.*"]
  workflow_dispatch:
    inputs:
      sha:
        description: "Commit SHA of the staging image to promote"
        required: true

concurrency:
  group: prod
  cancel-in-progress: false

permissions:
  contents: read
  id-token: write

jobs:
  promote:
    runs-on: ubuntu-latest
    environment: prod  # GitHub Environments → "Required reviewers" gates this
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_DEPLOY_SA }}
      - uses: google-github-actions/setup-gcloud@v2
      - run: gcloud auth configure-docker us-central1-docker.pkg.dev
      - name: Retag staging images as prod
        run: |
          SHA="${{ inputs.sha || github.sha }}"
          for svc in api mcp; do
            SRC="us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/lockin/${svc}:${SHA}"
            DST="us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/lockin/${svc}:${GITHUB_REF_NAME}"
            gcloud artifacts docker tags add "$SRC" "$DST"
          done
      - uses: google-github-actions/get-gke-credentials@v2
        with:
          cluster_name: lockin-prod
          location: us-central1
      - name: Roll prod deployments
        run: |
          for svc in api mcp; do
            kubectl set image deploy/${svc} ${svc}="us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/lockin/${svc}:${GITHUB_REF_NAME}" -n lockin
            kubectl rollout status deploy/${svc} -n lockin --timeout=600s
          done
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_WEB_PROJECT_ID }}
          working-directory: apps/web
          vercel-args: "--prod"
```

- [ ] **Step 3: Document the GitHub Environments setup**

In `docs/handoffs/week-1-2.md`, note that the `prod` GitHub Environment requires manual reviewer approval — the workflow file alone does not enforce that; configure in repo Settings → Environments.

- [ ] **Step 4: Commit**

```pwsh
git add .github/workflows/staging.yml .github/workflows/prod.yml
git commit -m "ci: staging deploy on main + prod promotion on tag"
```

---

## Task 7 — Terraform: GCP modules + staging/prod envs

**Why:** Acceptance #3 — `terraform apply` produces a working staging environment from zero; `destroy` cleans up.

**Files:**
- Create: `infra/terraform/modules/{vpc,postgres,redis,kubernetes,secrets,dns}/{main.tf,variables.tf,outputs.tf,versions.tf}`
- Create: `infra/terraform/envs/{staging,prod}/{main.tf,backend.tf,terraform.tfvars.example}`
- Create: `infra/terraform/README.md`

- [ ] **Step 1: Bootstrap state bucket** (one-time, manual — document only)

```pwsh
# Run once per project. Bucket holds Terraform state for both envs.
gcloud storage buckets create gs://lockin-tfstate-${env:LOCKIN_GCP_PROJECT} `
  --project=$env:LOCKIN_GCP_PROJECT `
  --location=us-central1 `
  --uniform-bucket-level-access `
  --public-access-prevention
gcloud storage buckets update gs://lockin-tfstate-${env:LOCKIN_GCP_PROJECT} --versioning
```

Document this in `infra/terraform/README.md`. Do **not** automate it — bootstrapping state from code is a chicken-and-egg problem.

- [ ] **Step 2: `infra/terraform/modules/vpc/`**

`main.tf`:
```hcl
resource "google_compute_network" "this" {
  name                    = "${var.name}-vpc"
  project                 = var.project_id
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "primary" {
  name          = "${var.name}-primary"
  project       = var.project_id
  region        = var.region
  network       = google_compute_network.this.id
  ip_cidr_range = var.primary_cidr
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = var.pods_cidr
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = var.services_cidr
  }
  private_ip_google_access = true
}

resource "google_compute_router" "nat_router" {
  name    = "${var.name}-nat-router"
  project = var.project_id
  region  = var.region
  network = google_compute_network.this.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "${var.name}-nat"
  project                            = var.project_id
  region                             = var.region
  router                             = google_compute_router.nat_router.name
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

resource "google_compute_global_address" "private_service_access" {
  name          = "${var.name}-psa"
  project       = var.project_id
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.this.id
}

resource "google_service_networking_connection" "psa" {
  network                 = google_compute_network.this.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_access.name]
}
```

`variables.tf`:
```hcl
variable "project_id" { type = string }
variable "name"       { type = string }
variable "region"     { type = string }
variable "primary_cidr"  { type = string default = "10.10.0.0/20" }
variable "pods_cidr"     { type = string default = "10.20.0.0/14" }
variable "services_cidr" { type = string default = "10.24.0.0/20" }
```

`outputs.tf`:
```hcl
output "network_id"        { value = google_compute_network.this.id }
output "network_self_link" { value = google_compute_network.this.self_link }
output "subnet_self_link"  { value = google_compute_subnetwork.primary.self_link }
output "psa_connection"    { value = google_service_networking_connection.psa.id }
```

`versions.tf`:
```hcl
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    google = { source = "hashicorp/google", version = ">= 5.40, < 6.0" }
  }
}
```

- [ ] **Step 3: `infra/terraform/modules/postgres/`** (Cloud SQL with TimescaleDB)

`main.tf`:
```hcl
resource "google_sql_database_instance" "this" {
  name             = var.name
  project          = var.project_id
  region           = var.region
  database_version = "POSTGRES_16"
  deletion_protection = var.deletion_protection

  settings {
    tier              = var.tier
    availability_type = var.availability_type
    disk_size         = var.disk_size_gb
    disk_autoresize   = true
    disk_type         = "PD_SSD"

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = var.network_self_link
      enable_private_path_for_google_cloud_services = true
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = var.backup_retention_count
      }
    }

    database_flags {
      name  = "cloudsql.enable_pg_cron"
      value = "on"
    }
    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }
    database_flags {
      # TimescaleDB is on the Cloud SQL preinstalled extensions list as of 2025.
      name  = "cloudsql.enable_pglogical"
      value = "on"
    }

    insights_config {
      query_insights_enabled  = true
      record_application_tags = true
      record_client_address   = false
    }
  }
}

resource "google_sql_database" "app" {
  name     = "lockin"
  project  = var.project_id
  instance = google_sql_database_instance.this.name
}

resource "random_password" "app_user" {
  length  = 32
  special = true
}

resource "google_sql_user" "app" {
  name     = "lockin_app"
  project  = var.project_id
  instance = google_sql_database_instance.this.name
  password = random_password.app_user.result
}
```

`variables.tf`:
```hcl
variable "project_id"            { type = string }
variable "name"                  { type = string }
variable "region"                { type = string }
variable "network_self_link"     { type = string }
variable "tier"                  { type = string default = "db-custom-2-7680" }
variable "availability_type"     { type = string default = "ZONAL" }
variable "disk_size_gb"          { type = number default = 50 }
variable "backup_retention_count"{ type = number default = 7 }
variable "deletion_protection"   { type = bool   default = true }
```

`outputs.tf`:
```hcl
output "instance_name"        { value = google_sql_database_instance.this.name }
output "connection_name"      { value = google_sql_database_instance.this.connection_name }
output "private_ip"           { value = google_sql_database_instance.this.private_ip_address }
output "app_user_password"    { value = random_password.app_user.result sensitive = true }
output "database_name"        { value = google_sql_database.app.name }
```

`versions.tf`:
```hcl
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    google = { source = "hashicorp/google", version = ">= 5.40, < 6.0" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}
```

> **TimescaleDB activation:** After `terraform apply` provisions the instance, run once via `gcloud sql connect`: `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;`. Document in module README.

- [ ] **Step 4: `infra/terraform/modules/redis/`** (Memorystore)

`main.tf`:
```hcl
resource "google_redis_instance" "this" {
  name           = var.name
  project        = var.project_id
  region         = var.region
  tier           = var.tier              # BASIC for staging, STANDARD_HA for prod
  memory_size_gb = var.memory_size_gb
  redis_version  = "REDIS_7_2"

  authorized_network      = var.network_id
  connect_mode            = "PRIVATE_SERVICE_ACCESS"
  reserved_ip_range       = var.reserved_ip_range
  transit_encryption_mode = "SERVER_AUTHENTICATION"
  auth_enabled            = true

  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time { hours = 4, minutes = 0, seconds = 0, nanos = 0 }
    }
  }
}
```

`variables.tf`:
```hcl
variable "project_id"        { type = string }
variable "name"              { type = string }
variable "region"            { type = string }
variable "network_id"        { type = string }
variable "tier"              { type = string default = "BASIC" }
variable "memory_size_gb"    { type = number default = 1 }
variable "reserved_ip_range" { type = string default = "10.30.0.0/29" }
```

`outputs.tf`:
```hcl
output "host"      { value = google_redis_instance.this.host }
output "port"      { value = google_redis_instance.this.port }
output "auth_string" { value = google_redis_instance.this.auth_string sensitive = true }
```

- [ ] **Step 5: `infra/terraform/modules/kubernetes/`** (GKE Autopilot — fewer knobs, matches the "no premature optimization" rule)

`main.tf`:
```hcl
resource "google_service_account" "node_sa" {
  account_id   = "${var.name}-gke-node"
  display_name = "GKE node SA for ${var.name}"
  project      = var.project_id
}

resource "google_container_cluster" "this" {
  name     = var.name
  project  = var.project_id
  location = var.region

  enable_autopilot = true
  network          = var.network_self_link
  subnetwork       = var.subnet_self_link

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  release_channel { channel = "REGULAR" }

  workload_identity_config { workload_pool = "${var.project_id}.svc.id.goog" }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.master_cidr
  }

  deletion_protection = var.deletion_protection
}
```

`variables.tf`:
```hcl
variable "project_id"          { type = string }
variable "name"                { type = string }
variable "region"              { type = string }
variable "network_self_link"   { type = string }
variable "subnet_self_link"    { type = string }
variable "master_cidr"         { type = string default = "172.16.0.0/28" }
variable "deletion_protection" { type = bool   default = true }
```

`outputs.tf`:
```hcl
output "name"        { value = google_container_cluster.this.name }
output "endpoint"    { value = google_container_cluster.this.endpoint sensitive = true }
output "ca_cert"     { value = google_container_cluster.this.master_auth[0].cluster_ca_certificate sensitive = true }
```

- [ ] **Step 6: `infra/terraform/modules/secrets/`**

`main.tf`:
```hcl
resource "google_secret_manager_secret" "this" {
  for_each  = toset(var.secret_ids)
  project   = var.project_id
  secret_id = each.value
  replication {
    auto {}
  }
}

resource "google_service_account" "app" {
  for_each     = toset(var.app_service_accounts)
  project      = var.project_id
  account_id   = each.value
  display_name = "App SA: ${each.value}"
}

resource "google_secret_manager_secret_iam_member" "access" {
  for_each = {
    for pair in flatten([
      for secret in var.secret_ids : [
        for sa in var.app_service_accounts : {
          key = "${secret}::${sa}", secret = secret, sa = sa
        }
      ]
    ]) : pair.key => pair
  }
  project   = var.project_id
  secret_id = google_secret_manager_secret.this[each.value.secret].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app[each.value.sa].email}"
}
```

`variables.tf`:
```hcl
variable "project_id"           { type = string }
variable "secret_ids"            { type = list(string) }
variable "app_service_accounts"  { type = list(string) }
```

`outputs.tf`:
```hcl
output "secret_names" {
  value = { for k, s in google_secret_manager_secret.this : k => s.name }
}
output "service_account_emails" {
  value = { for k, sa in google_service_account.app : k => sa.email }
}
```

- [ ] **Step 7: `infra/terraform/modules/dns/`**

`main.tf`:
```hcl
resource "google_dns_managed_zone" "this" {
  name        = var.zone_name
  project     = var.project_id
  dns_name    = var.dns_name
  description = "LockIn ${var.env} zone"
  visibility  = "public"
  dnssec_config { state = "on" }
}
```

`variables.tf`:
```hcl
variable "project_id" { type = string }
variable "zone_name"  { type = string }
variable "dns_name"   { type = string }  # must end in "."
variable "env"        { type = string }
```

`outputs.tf`:
```hcl
output "name_servers" { value = google_dns_managed_zone.this.name_servers }
output "zone_name"    { value = google_dns_managed_zone.this.name }
```

- [ ] **Step 8: `infra/terraform/envs/staging/backend.tf`**

```hcl
terraform {
  backend "gcs" {
    bucket = "lockin-tfstate-PROJECT_ID_HERE"  # replace via `-backend-config`
    prefix = "envs/staging"
  }
}
```

> Init pattern (run once per machine):
> `terraform init -backend-config="bucket=lockin-tfstate-${LOCKIN_GCP_PROJECT}"`

- [ ] **Step 9: `infra/terraform/envs/staging/main.tf`**

```hcl
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    google = { source = "hashicorp/google", version = ">= 5.40, < 6.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" { type = string }
variable "region"     { type = string default = "us-central1" }
variable "dns_name"   { type = string default = "staging.lockin.app." }

module "vpc" {
  source     = "../../modules/vpc"
  project_id = var.project_id
  name       = "lockin-staging"
  region     = var.region
}

module "postgres" {
  source            = "../../modules/postgres"
  project_id        = var.project_id
  name              = "lockin-staging-pg"
  region            = var.region
  network_self_link = module.vpc.network_self_link
  tier              = "db-custom-2-7680"
  availability_type = "ZONAL"
  deletion_protection = false   # staging may be rebuilt
}

module "redis" {
  source         = "../../modules/redis"
  project_id     = var.project_id
  name           = "lockin-staging-redis"
  region         = var.region
  network_id     = module.vpc.network_id
  tier           = "BASIC"
  memory_size_gb = 1
}

module "k8s" {
  source              = "../../modules/kubernetes"
  project_id          = var.project_id
  name                = "lockin-staging"
  region              = var.region
  network_self_link   = module.vpc.network_self_link
  subnet_self_link    = module.vpc.subnet_self_link
  deletion_protection = false
}

module "secrets" {
  source     = "../../modules/secrets"
  project_id = var.project_id
  secret_ids = [
    "DATABASE_URL", "REDIS_URL", "NEXTAUTH_SECRET",
    "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET",
    "SENTRY_DSN_WEB", "SENTRY_DSN_API", "SENTRY_DSN_MCP",
    "GRAFANA_CLOUD_OTLP_ENDPOINT", "GRAFANA_CLOUD_OTLP_AUTH",
  ]
  app_service_accounts = ["lockin-api", "lockin-mcp", "lockin-deploy"]
}

module "dns" {
  source     = "../../modules/dns"
  project_id = var.project_id
  zone_name  = "lockin-staging"
  dns_name   = var.dns_name
  env        = "staging"
}

output "name_servers"         { value = module.dns.name_servers }
output "postgres_connection"  { value = module.postgres.connection_name }
output "gke_endpoint"         { value = module.k8s.endpoint sensitive = true }
```

`terraform.tfvars.example`:
```hcl
project_id = "lockin-staging-XXXXXX"
region     = "us-central1"
dns_name   = "staging.lockin.app."
```

- [ ] **Step 10: `infra/terraform/envs/prod/`**

Same shape as staging with tier overrides:
- `availability_type = "REGIONAL"` on postgres
- `tier = "STANDARD_HA"` + `memory_size_gb = 4` on redis
- `deletion_protection = true` everywhere
- `dns_name = "lockin.app."`
- backend prefix `envs/prod`

(Full file mirrors staging; copy + adjust the four values above.)

- [ ] **Step 11: `infra/terraform/README.md`**

Document: state bucket bootstrap, `terraform init -backend-config=...` pattern, plan/apply/destroy workflow, TimescaleDB `CREATE EXTENSION` step, the fact that Workload Identity Federation for GitHub Actions OIDC needs to be set up once per project (separate ADR), and the cleanup checklist (delete state files in GCS *after* `destroy` for absolute zero remnants).

- [ ] **Step 12: Local validation**

```pwsh
terraform -chdir=infra/terraform fmt -recursive
terraform -chdir=infra/terraform/envs/staging init -backend=false
terraform -chdir=infra/terraform/envs/staging validate
terraform -chdir=infra/terraform/envs/prod init -backend=false
terraform -chdir=infra/terraform/envs/prod validate
```

Expected: fmt is clean, both envs validate.

- [ ] **Step 13: Commit**

```pwsh
git add infra/terraform
git commit -m "infra(terraform): GCP modules (vpc, postgres, redis, gke, secrets, dns) + envs"
```

---

## Task 8 — Secret management + `pnpm secrets:pull`

**Why:** Acceptance #5 — zero secrets in repo; rotation works without redeploy.

**Files:**
- Create: `scripts/secrets-pull.mjs`
- Modify: `.env.example` (expand with all needed keys)
- Modify: `apps/api/app/core/config.py` and `apps/mcp/app/core/config.py` to read from env (already do)
- Document GCP service-account workload-identity setup in `infra/terraform/README.md` (Task 7 stub)

- [ ] **Step 1: `scripts/secrets-pull.mjs`**

```js
#!/usr/bin/env node
// Pulls dev secrets from Google Secret Manager into .env.local.
// Requires: gcloud auth application-default login.
// Required env: LOCKIN_GCP_PROJECT (e.g. "lockin-staging-XXXXXX").

import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";

const project = process.env.LOCKIN_GCP_PROJECT;
if (!project) {
  console.error("LOCKIN_GCP_PROJECT must be set.");
  process.exit(1);
}

const secrets = [
  "DATABASE_URL", "REDIS_URL", "NEXTAUTH_SECRET",
  "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET",
  "SENTRY_DSN_WEB", "SENTRY_DSN_API", "SENTRY_DSN_MCP",
  "GRAFANA_CLOUD_OTLP_ENDPOINT", "GRAFANA_CLOUD_OTLP_AUTH",
];

const lines = [];
for (const name of secrets) {
  try {
    const value = execFileSync(
      "gcloud",
      ["secrets", "versions", "access", "latest", `--secret=${name}`, `--project=${project}`],
      { encoding: "utf-8" },
    ).trimEnd();
    lines.push(`${name}=${value}`);
    process.stdout.write(`  ✓ ${name}\n`);
  } catch (err) {
    process.stdout.write(`  ✗ ${name} (missing in Secret Manager — skipping)\n`);
  }
}
writeFileSync(".env.local", lines.join("\n") + "\n", { mode: 0o600 });
console.log("\nWrote .env.local (mode 0600).");
```

- [ ] **Step 2: Expand `.env.example`**

```
# Local dev — pulled via `pnpm secrets:pull` after `gcloud auth application-default login`.
# Pattern: postgresql://<user>:<password>@localhost:5432/lockin  (see existing .env.example)
DATABASE_URL=
TIMESCALE_URL=
REDIS_URL=redis://localhost:6379

# NextAuth + Google OAuth (Google Cloud Console → APIs & Services → Credentials)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
NEXTAUTH_SECRET=
NEXTAUTH_URL=http://localhost:3000

# Observability
SENTRY_DSN_WEB=
SENTRY_DSN_API=
SENTRY_DSN_MCP=
GRAFANA_CLOUD_OTLP_ENDPOINT=
GRAFANA_CLOUD_OTLP_AUTH=

# Optional (Slice 5+)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
```

- [ ] **Step 3: Acceptance verification (manual)**

Document: rotate a staging secret with `gcloud secrets versions add`, then `pnpm secrets:pull` should pick up the new value. Running services on GKE read directly from Secret Manager via CSI driver or env injection (separate doc).

- [ ] **Step 4: Commit**

```pwsh
git add scripts/secrets-pull.mjs .env.example
git commit -m "feat(secrets): pnpm secrets:pull helper + expanded .env.example"
```

---

## Task 9 — NextAuth v5 + Google OAuth + JWT middleware

**Why:** Acceptance #6 — `/api/auth/signin/google` completes; `/api/me` returns the authed user.

**Files:**
- Modify: `apps/web/package.json` (add `next-auth@beta`, providers, JWT lib)
- Create: `apps/web/src/auth.ts`, `apps/web/src/app/api/auth/[...nextauth]/route.ts`
- Create: `apps/web/src/app/api/me/route.ts` (proxy to api `/v1/me`, attaching JWT)
- Create: `apps/web/src/middleware.ts`
- Create: `apps/api/app/core/auth.py`, `apps/api/app/api/v1/routes/me.py`
- Modify: `apps/api/app/api/v1/router.py` to include `me` router

- [ ] **Step 1: Install Auth.js v5 in `apps/web`**

Add to `apps/web/package.json` dependencies:
```json
"next-auth": "5.0.0-beta.25",
"@auth/core": "^0.37.4"
```

- [ ] **Step 2: `apps/web/src/auth.ts`**

```ts
import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: { params: { prompt: "consent", access_type: "offline" } },
    }),
  ],
  session: { strategy: "jwt", maxAge: 7 * 24 * 60 * 60 },
  jwt: { maxAge: 7 * 24 * 60 * 60 },
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account && profile) {
        token.providers = Array.from(new Set([...(token.providers as string[] ?? []), account.provider]));
        token.user_id = (profile.sub as string) ?? token.sub;
        token.email = profile.email as string;
      }
      return token;
    },
    async session({ session, token }) {
      session.user_id = token.user_id as string;
      session.providers = (token.providers as string[]) ?? [];
      return session;
    },
  },
  cookies: {
    sessionToken: {
      name: "__Secure-lockin.session-token",
      options: { httpOnly: true, sameSite: "lax", path: "/", secure: true },
    },
  },
});

declare module "next-auth" {
  interface Session {
    user_id: string;
    providers: string[];
  }
}
```

- [ ] **Step 3: `apps/web/src/app/api/auth/[...nextauth]/route.ts`**

```ts
import { handlers } from "@/auth";
export const { GET, POST } = handlers;
```

- [ ] **Step 4: `apps/web/src/middleware.ts`**

```ts
import { auth } from "@/auth";

export default auth((req) => {
  const isProtected = req.nextUrl.pathname.startsWith("/dashboard") ||
                      req.nextUrl.pathname.startsWith("/api/me");
  if (isProtected && !req.auth) {
    const url = new URL("/api/auth/signin", req.nextUrl.origin);
    return Response.redirect(url);
  }
});

export const config = {
  matcher: ["/dashboard/:path*", "/api/me/:path*"],
};
```

- [ ] **Step 5: `apps/web/src/app/api/me/route.ts`** (proves end-to-end)

```ts
import { auth } from "@/auth";

export const GET = auth(async (req) => {
  if (!req.auth) return new Response("unauthorized", { status: 401 });
  return Response.json({
    user_id: req.auth.user_id,
    email: req.auth.user?.email,
    providers: req.auth.providers,
  });
});
```

- [ ] **Step 6: `apps/api/app/core/auth.py`** (validates the Auth.js JWT server-side for direct API calls from non-web clients)

```python
"""JWT validation for the API.

NextAuth issues HS256-signed JWTs using NEXTAUTH_SECRET. The API verifies the
same secret. For non-Google providers added in the Week 5 polish window, this
file should be re-evaluated.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings


class CurrentUser(BaseModel):
    user_id: str
    email: str
    providers: list[str]


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer")
    token = authorization.split(" ", 1)[1]
    try:
        claims = jwt.decode(
            token, settings.NEXTAUTH_SECRET, algorithms=["HS256"], options={"verify_aud": False}
        )
    except JWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token") from exc
    return CurrentUser(
        user_id=claims["user_id"],
        email=claims.get("email", ""),
        providers=list(claims.get("providers", [])),
    )
```

- [ ] **Step 7: `apps/api/app/api/v1/routes/me.py`**

```python
from fastapi import APIRouter, Depends

from app.core.auth import CurrentUser, get_current_user

router = APIRouter(tags=["me"])


@router.get("/me", response_model=CurrentUser)
async def me(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return user
```

Wire into `apps/api/app/api/v1/router.py`:
```python
from app.api.v1.routes import health, me
api_router.include_router(me.router, prefix="/v1")
```

- [ ] **Step 8: Acceptance test — manual**

```pwsh
pnpm -F @lockin/web dev   # in one shell
# In a browser: visit http://localhost:3000/api/auth/signin/google
# Complete OAuth. Browser is redirected back.
# Then GET http://localhost:3000/api/me → JSON with user_id, email, providers: ["google"].
```

- [ ] **Step 9: Commit**

```pwsh
git add apps/web/src/auth.ts apps/web/src/middleware.ts apps/web/src/app/api/auth apps/web/src/app/api/me apps/api/app/core/auth.py apps/api/app/api/v1/routes/me.py apps/api/app/api/v1/router.py apps/web/package.json
git commit -m "feat(auth): NextAuth v5 + Google OAuth + JWT middleware"
```

---

## Task 10 — WebAuthn / Passkey endpoints

**Why:** Acceptance #6 — passkey registration endpoint accepts an attestation and persists it.

**Files:**
- Modify: `apps/web/package.json` — add `@simplewebauthn/server`, `@simplewebauthn/browser`
- Create: `apps/web/src/app/api/webauthn/register/options/route.ts`
- Create: `apps/web/src/app/api/webauthn/register/verify/route.ts`
- Modify: `apps/api/pyproject.toml` — add `webauthn>=2.0`
- Create: `apps/api/app/api/v1/routes/webauthn.py`
- Create: `apps/api/app/db/models/credential.py`
- Create: `apps/api/alembic/versions/0002_webauthn_credentials.py`

- [ ] **Step 1: Add webauthn deps**

`apps/web/package.json` dependencies:
```json
"@simplewebauthn/server": "^11.0.0",
"@simplewebauthn/browser": "^11.0.0"
```

`apps/api/pyproject.toml` dependencies:
```toml
"webauthn>=2.5",
```

- [ ] **Step 2: SQLAlchemy model `apps/api/app/db/models/credential.py`**

```python
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import LargeBinary, String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WebauthnCredential(Base):
    __tablename__ = "webauthn_credentials"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), index=True, nullable=False)
    credential_id: Mapped[bytes] = mapped_column(LargeBinary, unique=True, nullable=False)
    public_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    sign_count: Mapped[int] = mapped_column(default=0, nullable=False)
    transports: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now())
```

- [ ] **Step 3: Alembic migration**

```python
"""webauthn credentials

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0002"
down_revision = "0001"

def upgrade() -> None:
    op.create_table(
        "webauthn_credentials",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("credential_id", sa.LargeBinary, nullable=False, unique=True),
        sa.Column("public_key", sa.LargeBinary, nullable=False),
        sa.Column("sign_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("transports", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table("webauthn_credentials")
```

- [ ] **Step 4: API routes `apps/api/app/api/v1/routes/webauthn.py`**

```python
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from webauthn import generate_registration_options, verify_registration_response
from webauthn.helpers.structs import PublicKeyCredentialCreationOptions

from app.api.v1.deps import get_db_session
from app.core.auth import CurrentUser, get_current_user
from app.core.config import settings
from app.db.models.credential import WebauthnCredential

router = APIRouter(prefix="/webauthn", tags=["webauthn"])

RP_ID = settings.WEBAUTHN_RP_ID
RP_NAME = "LockIn"


@router.post("/register/options")
async def register_options(user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=user.user_id.encode("utf-8"),
        user_name=user.email,
    )
    return options.model_dump(mode="json")


@router.post("/register/verify")
async def register_verify(
    body: dict[str, Any],
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    try:
        verification = verify_registration_response(
            credential=body["credential"],
            expected_challenge=bytes.fromhex(body["challenge"]),
            expected_rp_id=RP_ID,
            expected_origin=settings.WEBAUTHN_EXPECTED_ORIGIN,
        )
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    cred = WebauthnCredential(
        user_id=user.user_id,
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        transports=",".join(body.get("transports", [])) or None,
    )
    db.add(cred)
    await db.commit()
    return {"status": "registered"}
```

Add `WEBAUTHN_RP_ID` and `WEBAUTHN_EXPECTED_ORIGIN` to `app/core/config.py` and to `.env.example`:
```
WEBAUTHN_RP_ID=localhost
WEBAUTHN_EXPECTED_ORIGIN=http://localhost:3000
```

- [ ] **Step 5: Mirror options/verify proxies in `apps/web`** so the browser hits same-origin endpoints. Each `apps/web/src/app/api/webauthn/register/*/route.ts` forwards to the api with the user's JWT in the `Authorization` header.

- [ ] **Step 6: Acceptance** — POST a manufactured attestation; expect `{ "status": "registered" }` and a row in `webauthn_credentials`.

- [ ] **Step 7: Commit**

```pwsh
git add apps/web/src/app/api/webauthn apps/api/app/db/models/credential.py apps/api/alembic/versions/0002_webauthn_credentials.py apps/api/app/api/v1/routes/webauthn.py apps/api/app/core/config.py apps/api/pyproject.toml apps/web/package.json .env.example
git commit -m "feat(auth): WebAuthn passkey registration endpoints"
```

---

## Task 11 — OpenTelemetry on `apps/api` + `apps/mcp` (Grafana Cloud exporter)

**Why:** Acceptance #4 — OTel trace shows the request in Grafana within 60s of a forced 500.

**Files:**
- Modify: `apps/api/pyproject.toml`, `apps/mcp/pyproject.toml` — add OTLP exporter deps
- Create: `apps/api/app/core/observability.py`, `apps/mcp/app/core/observability.py`
- Modify: `apps/api/app/main.py`, `apps/mcp/app/main.py` — bootstrap OTel in lifespan

- [ ] **Step 1: Deps**

Append to `apps/api/pyproject.toml` and `apps/mcp/pyproject.toml` dependencies:
```toml
"opentelemetry-exporter-otlp-proto-http>=1.28",
"opentelemetry-instrumentation-httpx>=0.49b0",
"opentelemetry-instrumentation-redis>=0.49b0",
"opentelemetry-instrumentation-sqlalchemy>=0.49b0",  # api only
```

- [ ] **Step 2: `apps/api/app/core/observability.py`**

```python
"""Wire OpenTelemetry once at startup.

Exports to Grafana Cloud's OTLP HTTP endpoint. Auth is a single header (base64
of "instance_id:token") supplied via GRAFANA_CLOUD_OTLP_AUTH. The endpoint
itself comes from GRAFANA_CLOUD_OTLP_ENDPOINT.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import settings


def configure_observability(app) -> None:
    if not settings.GRAFANA_CLOUD_OTLP_ENDPOINT:
        return  # OTel is opt-in; no exporter configured → no-op

    resource = Resource.create({
        "service.name": "lockin-api",
        "service.version": settings.APP_VERSION,
        "deployment.environment": settings.ENV,
    })
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=f"{settings.GRAFANA_CLOUD_OTLP_ENDPOINT}/v1/traces",
        headers={"Authorization": f"Basic {settings.GRAFANA_CLOUD_OTLP_AUTH}"},
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    RedisInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()
```

- [ ] **Step 3: Call `configure_observability(fast_app)` in `apps/api/app/main.py` after `register_exception_handlers(...)`**

- [ ] **Step 4: Mirror for `apps/mcp/app/core/observability.py`** (drop SQLAlchemy + Redis instrumentations, keep httpx + FastAPI/Starlette)

- [ ] **Step 5: Add env vars to `.env.example` and `app/core/config.py`** for `GRAFANA_CLOUD_OTLP_ENDPOINT`, `GRAFANA_CLOUD_OTLP_AUTH`, `APP_VERSION`, `ENV`

- [ ] **Step 6: Commit**

```pwsh
git add apps/api apps/mcp .env.example
git commit -m "feat(observability): OpenTelemetry → Grafana Cloud OTLP HTTP"
```

---

## Task 12 — Sentry on web/api/mcp + release tagging by git SHA

**Files:**
- Modify: `apps/web/package.json` — add `@sentry/nextjs`
- Create: `apps/web/sentry.{client,server,edge}.config.ts`, `apps/web/instrumentation.ts`, `apps/web/next.config.ts` (wrap)
- Modify: `apps/api/pyproject.toml`, `apps/mcp/pyproject.toml` — `sentry-sdk[fastapi]>=2.18`
- Modify: `apps/api/app/main.py`, `apps/mcp/app/main.py` — `sentry_sdk.init(...)` in lifespan

- [ ] **Step 1: Web — install `@sentry/nextjs` and run `npx @sentry/wizard` artifacts**

`apps/web/sentry.client.config.ts`:
```ts
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  release: process.env.NEXT_PUBLIC_GIT_SHA,
  environment: process.env.NEXT_PUBLIC_ENV ?? "development",
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0,
  replaysOnErrorSampleRate: 1.0,
});
```

Mirror `sentry.server.config.ts` and `sentry.edge.config.ts` (no replay).

`apps/web/next.config.ts` — wrap with `withSentryConfig`. Pass `release` from `NEXT_PUBLIC_GIT_SHA` (set in CI workflows already via `GITHUB_SHA`).

- [ ] **Step 2: API — `sentry_sdk.init` before `configure_observability`**

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.SENTRY_DSN_API:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN_API,
        release=settings.GIT_SHA,
        environment=settings.ENV,
        traces_sample_rate=0.1,
        integrations=[FastApiIntegration()],
    )
```

- [ ] **Step 3: MCP — same pattern (Starlette/FastAPI integration)**

- [ ] **Step 4: Commit**

```pwsh
git add apps/web/sentry*.config.ts apps/web/next.config.ts apps/web/package.json apps/api apps/mcp
git commit -m "feat(observability): Sentry SDK on web/api/mcp with release tagging"
```

---

## Task 13 — Grafana Cloud dashboards + Slack alert + forced-500 verification

**Files:**
- Create: `infra/grafana/dashboards/{api-golden-signals,postgres-health,mcp-health}.json`
- Document: dashboard import process in `infra/grafana/README.md`

- [ ] **Step 1: Author dashboard JSON** — three Grafana dashboards exported as JSON. Use the Grafana UI to author once, then export. Each lives under `infra/grafana/dashboards/`. Each dashboard is provisioned via Grafana Cloud's UI (the JSON files are the version-controlled source of truth; document import in README).

  - `api-golden-signals.json` — RED panels: request rate (by route), error rate (`status_code{ge=500}`), latency p50/p95/p99
  - `postgres-health.json` — connections, query latency, deadlocks, replication lag
  - `mcp-health.json` — tool-call rate, error rate, latency by tool name

- [ ] **Step 2: Slack alert channel** — create Grafana Slack contact point (`#lockin-test-alerts`) and a rule: "API 5xx error rate > 0% over 1m → fire".

- [ ] **Step 3: Acceptance test — force a 500**

In staging, hit a route that raises. Verify within 60s:
  - Sentry: issue with stack trace.
  - Grafana: error-rate panel rises; Slack alert fires.

Document the exact route used (e.g., `GET /v1/__force_500__` behind `ENV=staging` only).

- [ ] **Step 4: Commit**

```pwsh
git add infra/grafana
git commit -m "infra(observability): Grafana dashboards + Slack alert wiring"
```

---

## Task 14 — TimescaleDB hypertable migration (ready, unapplied)

**Why:** Acceptance #8 — TimescaleDB migration sits ready (Week 3 owns the first writes).

**Files:**
- Create: `apps/api/alembic/versions/0001_timescale_events_hypertable.py`

- [ ] **Step 1: Migration**

```python
"""timescale events hypertable

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0001"
down_revision = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    op.create_table(
        "events",
        sa.Column("event_id", UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("event_version", sa.Integer, nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("client_idempotency_key", sa.String(128), nullable=True),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.PrimaryKeyConstraint("event_id", "occurred_at"),
    )

    op.execute(
        "SELECT create_hypertable('events', 'occurred_at', chunk_time_interval => INTERVAL '7 days')"
    )

    op.create_index("ix_events_user_occurred", "events", ["user_id", "occurred_at"])
    op.create_index("ix_events_type_occurred", "events", ["event_type", "occurred_at"])
    op.create_unique_constraint(
        "uq_events_user_idem", "events", ["user_id", "client_idempotency_key"],
    )


def downgrade() -> None:
    op.drop_table("events")
```

> **Acceptance:** This migration is committed but NOT applied to staging in Week 1–2. Week 3 will apply it as part of the first `task.created` write path.

- [ ] **Step 2: Commit**

```pwsh
git add apps/api/alembic/versions/0001_timescale_events_hypertable.py
git commit -m "feat(db): TimescaleDB events hypertable migration (unapplied)"
```

---

## Task 15 — Wrap-up: decisions, handoff note, CURRENT_SLICE.md correction

**Files:**
- Create: `docs/decisions/2026-05-11-cloud-and-oauth.md`
- Create: `docs/handoffs/week-1-2.md`
- Modify: `docs/CURRENT_SLICE.md` — flip back to "Week 1–2 Foundation" until shipped, then update to Week 3

- [ ] **Step 1: `docs/decisions/2026-05-11-cloud-and-oauth.md`**

```markdown
# Cloud + OAuth decisions for P1 (2026-05-11)

## Cloud
**Choice:** GCP. Rationale: Vercel-adjacent latency for the web app; team familiarity; first-class Cloud SQL Postgres 16 + TimescaleDB; Memorystore for Redis Streams. AWS deferred.

## OAuth scope for P1
**Choice:** Google only. Apple + Microsoft are tracked for the Week 5 polish window. Rationale: ships Week 1–2 on schedule and matches CLAUDE.md's "Google only in P1" line.

## Implications
- Terraform modules target GCP only.
- `WORKLOAD_IDENTITY_PROVIDER` for GitHub Actions OIDC is GCP-only.
- Adding Apple/MS later costs ~1 day per provider plus a separate auth review.
```

- [ ] **Step 2: `docs/handoffs/week-1-2.md`**

```markdown
# Week 1–2 Foundation — Handoff to Week 3

## Shipped
- Turborepo + pnpm workspace at root; `pnpm install && pnpm dev` boots all three apps.
- Event schema v1 with 9 event types, Zod source-of-truth, generated TS + Python, round-trip tested both sides.
- `@lockin/ui` with `Button`, `Input`, `Card`, `Stack`, `Text`, `Icon` + Tailwind v4 tokens. Storybook preview deploys on PR.
- GitHub Actions: PR pipeline (paths-filtered), main → staging, tag → prod (manual approval).
- GCP Terraform modules: `vpc`, `postgres` (Cloud SQL + TimescaleDB), `redis`, `kubernetes` (GKE Autopilot), `secrets`, `dns`. Two envs.
- Secret Manager + `pnpm secrets:pull` helper.
- NextAuth v5 + Google OAuth + JWT middleware + `/api/me`. WebAuthn passkey registration.
- OpenTelemetry → Grafana Cloud; Sentry on web/api/mcp; Slack alert verified with forced-500.
- TimescaleDB `events` hypertable migration committed, unapplied.

## Open infra debt
- `prod` GitHub Environment manual reviewer approval is repo-setting; not enforced by workflow alone.
- TimescaleDB `CREATE EXTENSION` is a manual one-time step per Cloud SQL instance.
- Storybook deploys to a separate Vercel project — token + project id need to be provisioned in repo Secrets.
- Workload Identity Federation for GitHub OIDC to GCP: bootstrap doc in `infra/terraform/README.md` — must be done once.

## Week 3 starting state
- A user can sign up via Google and `/api/me` returns `{ user_id, email, providers: ["google"] }`.
- API can read `user_id` from `Authorization: Bearer <jwt>` and write to Postgres.
- Event schema is importable from `apps/web` (`import { TaskCreatedEvent } from "@lockin/events"`) and `apps/api` (`from lockin_events import TaskCreated`).
- `@lockin/ui` exports the components Week 3 needs for task capture: `Input`, `Button`, `Stack`, `Text`.
- Sentry + Grafana catch + display Week 3 errors.

## What Week 3 should NOT do
- Touch Terraform unless adding GKE workloads (Deployment manifests live in `apps/api/k8s/` and `apps/mcp/k8s/` — TBD).
- Promote `apps/api/app/events/schemas.py` further — it already re-exports from `lockin_events`.
- Add another OAuth provider — that's the Week 5 polish window.
```

- [ ] **Step 3: Update `docs/CURRENT_SLICE.md`**

Replace contents with the Week 1–2 foundation slice header until it ships, then flip to "Vertical Slice 0: Auth + Task Capture Spine" on close-out.

- [ ] **Step 4: Final commit**

```pwsh
git add docs/decisions docs/handoffs docs/CURRENT_SLICE.md
git commit -m "docs: Week 1–2 foundation decisions + handoff note"
```

---

## Self-review (run after writing this plan)

**Spec coverage:**
- [x] Deliverable 1 (Monorepo) → Task 1
- [x] Deliverable 2 (CI/CD) → Tasks 5 + 6
- [x] Deliverable 3 (Terraform) → Task 7
- [x] Deliverable 4 (Observability) → Tasks 11 + 12 + 13
- [x] Deliverable 5 (Secret management) → Task 8
- [x] Deliverable 6 (Auth foundation) → Tasks 9 + 10
- [x] Deliverable 7 (Design system) → Tasks 3 + 4
- [x] Deliverable 8 (Event schema v1) → Task 2 (+ Task 14 hypertable migration)

**Hard-constraint check:** No business logic; no scheduling, mood UI, LLM calls, or Calendar integration in any task. MCP server gets observability bootstrap only — no real tools.

**Decisions you may make alone / must escalate:** Decisions are recorded in `docs/decisions/2026-05-11-cloud-and-oauth.md`.

---

## Execution choice for the originating session

Md picked "Write a plan first, then execute the foundation-unblocking subset in this session." The subset is **Tasks 1, 2, 3, 5, 7, and 15** (Turborepo + event schema v1 + ui components + CI PR pipeline + Terraform skeleton + handoff/decisions docs). Tasks 4 (Storybook deploy), 6 (staging/prod CD), 8 (secrets CLI), 9–10 (auth + passkeys), 11–13 (full observability), and 14 (TimescaleDB migration) are sequenced for follow-up sessions per the handoff note above.

If the executor is a separate agent: use `superpowers:subagent-driven-development` to dispatch one task at a time with a review checkpoint between each.
