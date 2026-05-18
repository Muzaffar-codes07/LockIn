# LockIn — Claude Code Context

This file is loaded automatically by Claude Code. Keep it current; it's the single source of truth for AI-assisted work in this repo.

## What We're Building

LockIn is a **mood-and-energy-aware productivity agent** that schedules your day based on how you actually work, explains every decision, and exposes itself as an MCP tool callable by Claude, ChatGPT, and Gemini.

**The moat:** Longitudinal behavioral data (mood, energy, completion patterns over weeks/months) that general-purpose agents cannot replicate without capture infrastructure. The P1 product is the *wedge* that captures this data; the accumulated dataset over time is the *moat*. See [`docs/glossary.md`](docs/glossary.md) for the distinction.

**Platform strategy:** Web-first (Next.js + React), responsive for desktop and mobile browser. Native mobile deferred to P3.

## Non-Negotiable Principles (enforce in every review)

1. **Agent-native.** LockIn takes actions; it doesn't merely report.
2. **Memory-first.** Every user action is an immutable event. The behavior graph IS the product — not a task list.
3. **Explainable.** Every scheduling decision emits structured reasoning, not post-hoc justification.
4. **MCP is a first-class service**, not an adapter. Retrofitting costs 10x.
5. **Degrade gracefully.** ML offline → heuristics serve. Whisper down → text fallback. Calendar API rate-limited → cached data.
6. **Idempotent everything.** Every mutation API accepts a client-generated idempotency_key.
7. **On-device inference for mood/energy where feasible.** Privacy-first signal capture; cloud inference is a fallback, not a default.
8. **Voice and ambient capture as default input paths.** Text entry must always exist as fallback, but the agent assumes voice/ambient is primary.
9. **Open data portability.** Users can export their full behavioral graph on demand, in machine-readable form, within 24 hours.
10. **Behavioral data is never sold.** Codified in ToS. No data-broker integrations. No ad-tech. No "anonymized" resale loopholes.

## Tech Stack (Locked)

These choices are locked. Do not introduce alternatives without an ADR. This section is the single source of truth — the PRD defers here.

- **Frontend.** Use Next.js 16 with the App Router. React, Tailwind, TanStack Query, Zustand. Do not introduce another framework, state library, or CSS approach.
- **Auth.** Use NextAuth / Auth.js with OAuth 2.1 (Google first) plus Passkeys. Do not roll session/cookie logic by hand.
- **Backend.** Use FastAPI on Python 3.12+. Use Temporal for agent workflows. Do not add a second web framework or workflow engine.
- **Primary DB.** Use Postgres 16. Do not use SQLite or another RDBMS in any environment, including local dev.
- **Time-series.** Use TimescaleDB (Postgres extension). All time-series data goes here — not in a separate datastore.
- **Cache / streams.** Use Redis for caching and Redis Streams for event transport. Do not introduce Kafka, NATS, or RabbitMQ in P1.
- **ML.** Use LightGBM for scheduling decisions. Use Claude Haiku (preferred) or GPT-4o-mini for natural-language polish, via the LLM ports-and-adapters. Do not call LLM SDKs directly from services.
- **Voice (P1).** Use cloud Whisper. Fall back to Deepgram. Do not add a third transcription vendor. On-device Whisper is a P2+ target, not a P1 ship-blocker.
- **Mobile (P3 only).** Flutter when we get there. Do not start native mobile work in P1 or P2.
- **Infra.** Frontend on Vercel. Backend on GCP or AWS, Kubernetes, Terraform. No new cloud providers.
- **Observability.** OpenTelemetry traces and metrics, Grafana dashboards, Sentry for errors. No alternative APM.
- **MCP.** Dedicated MCP server as a separate binary (`apps/mcp`). Not a retrofit, not an adapter layer on the API.

## Repo Structure (Monorepo — Turborepo)

```
apps/
  web/         Next.js 16 app (frontend)
  api/         FastAPI gateway + services
  mcp/         MCP server (separate binary)
packages/
  shared-types/  TypeScript + Python type contracts
  ui/            Design system components (React + Tailwind)
  events/        Event schema (versioned)
docs/
  PRD.md                       Product requirements
  P1_Spec.md                   Phase 1 role-based spec
  Technical_Roadmap.md         12-month engineering plan
  Competitive_ReCut.md         Market positioning
```

## Current Phase: P1 — Foundation (Months 1–3)

**Mission:** Ship a responsive web MVP closing the loop: capture → mood check → schedule with explanation → learn. Expose MCP endpoint to Claude, ChatGPT, Gemini.

**Success gate:** 1,000 beta users · ≥50% accepted-schedule rate · W1 retention ≥45% desktop · MCP verified in Claude + ChatGPT + Gemini · p95 API <200ms · Lighthouse ≥90.

## What We Are NOT Building in P1

Do not let these sneak in, regardless of how easy they look:
- Gamification · streaks · badges
- 5-tier productivity classification
- Team features
- Outlook sync (Google only in P1)
- Native mobile (P3)
- Analytics dashboard
- Wearable integration
- Voice-based conversation (only voice capture)

## Event Schema Doctrine

The event schema is the most important artifact in the repo. Rules:
- Versioned from day one (`event_version: 1`)
- Forward-compatible field additions only
- Breaking changes require a migration path
- Every user action emits an event to Redis Streams → persisted to TimescaleDB (analytics) + Postgres (transactional state)

## Engineering Bar (applies to every PR)

- **Type safety end-to-end:** TypeScript strict mode, Pydantic for Python, shared types via `packages/shared-types`
- **No secrets in code, ever**
- **Idempotency keys on every mutation endpoint**
- **Structured logging** (OpenTelemetry) — no `print()`, no `console.log` in committed code
- **Tests are not optional** for business logic (scheduling, explanation, MCP tools)
- **Accessibility:** WCAG 2.2 AA from day one — no "we'll fix it in P3"

## How to Use Claude Code in This Repo

1. **Read `docs/` first** before starting any non-trivial feature
2. **Work in vertical slices**: auth → one capture path → one DB write → one UI render. Don't build layers in isolation.
3. **Reference event schema** (`packages/events/`) before adding any new user-facing action
4. **Ask before introducing new dependencies** — stack is deliberately constrained
5. **Flag scope creep immediately** — if a task grows beyond its slice, stop and escalate

## Current Working Context

The Week 1–2 Foundation slice is **complete** (all 8 deliverables on `main`, 2026-05-18). Active work is now **Vertical Slice 0 — Auth + Task Capture Spine**.

See `docs/CURRENT_SLICE.md` for what we're actively building right now, and `docs/handoffs/week-1-2.md` for the foundation outcome + remaining operational steps.
