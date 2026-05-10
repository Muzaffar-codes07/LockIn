# LockIn — Phase 1 Spec (Role-Based)
**Phase 1 · Months 1–3 · MVP**
**Companion to:** PRD v2, Scope Memo v2

---

## P1 Mission
Ship a focused agent that captures tasks via voice or text, syncs calendar, checks mood and energy, and schedules work with explainable AI reasoning. Expose an MCP endpoint so LockIn is callable from Claude, ChatGPT, and Gemini.

## Core Loop We Are Building
1. User captures a task (voice or text, under 10 seconds)
2. User does a mood and energy check (two taps, under 5 seconds)
3. LockIn schedules the task with a one-line "why"
4. User accepts, modifies, or rejects
5. LockIn learns

## Team Composition (8 people total)
1 PM · 1 Designer · 2 Mobile (Flutter) · 2 Backend · 1 ML · 1 DevOps/Agent Infra

---

## Product Management

**Owner:** PM Lead
**North Star for P1:** Accepted-schedule rate ≥ 50% by beta end

### Deliverables
- **Weeks 1–2:** Final user flows (capture, check-in, schedule, explain), acceptance criteria per feature, beta recruitment plan (target 200 alpha → 1,000 beta)
- **Weeks 3–6:** Weekly user interviews (minimum 5/week), scope-cut decisions, prioritization reviews
- **Weeks 7–10:** Beta launch plan, metrics instrumentation spec, post-P1 pricing decision
- **Weeks 11–12:** Launch communications, feedback ops, P2 scope draft

### Dependencies
Design (flows), Backend (instrumentation), DevOps (analytics pipeline)

### Definition of Done
Beta live · ≥500 weekly active users · 3 validated retention cohorts · P2 scope ratified

---

## Design

**Owner:** Design Lead (UX + UI combined for P1)

### Deliverables
- **Weeks 1–3:** User flow diagrams, wireframes for all core screens, design system tokens (colors, type, spacing, motion), mood/energy capture micro-interaction, explanation UI pattern
- **Weeks 4–8:** High-fidelity mockups, animation specs, voice input state design, onboarding sequence (≤90 sec to first scheduled task)
- **Weeks 9–12:** Accessibility audit (WCAG 2.2 AA), dark mode, edge states, app store assets

### Key Design Bets
- Explanation panel is **persistent, not hidden**
- Mood/energy uses **3 taps max**, no text entry required
- Voice is **first-class**, typing is fallback

### Definition of Done
Design system shipped · all P1 screens finalized · a11y passed · app store assets delivered

---

## Engineering — Backend

**Owner:** Backend Lead (2 engineers total)
**Stack:** FastAPI · Postgres 16 · TimescaleDB · Redis · Temporal (agent workflows)

### Deliverables
- **Weeks 1–3:** Auth (Passkeys + OAuth 2.1 for Google/Apple), API schema (tasks, mood, energy, schedule, explanations), databases provisioned, event bus (Redis Streams)
- **Weeks 4–7:** Google Calendar bidirectional sync, MCP server exposing core tools, voice transcription pipeline (Whisper or Deepgram fallback)
- **Weeks 8–10:** Scheduling service, explanation generation service, push notifications (FCM + APNs)
- **Weeks 11–12:** Performance hardening (p95 < 200ms), rate limiting, audit logging, load testing

### MCP Endpoint Spec (Critical P1 Deliverable)
- **Tools exposed:** `get_schedule`, `add_task`, `log_mood`, `explain_next_action`
- **Auth:** OAuth 2.1 device flow
- **Validation:** Must work inside Claude Desktop, ChatGPT, and Gemini by P1 ship

### Definition of Done
99.9% uptime in beta · MCP verified against Claude + ChatGPT · E2E test coverage · p95 < 200ms

---

## Engineering — Mobile

**Owner:** Mobile Lead (2 engineers, Flutter)

### Deliverables
- **Weeks 1–3:** Flutter project scaffolding, design system implementation, auth flow, navigation shell, offline-first data layer (Isar or Drift)
- **Weeks 4–7:** Task capture (text + voice with on-device fallback), mood/energy check-in, schedule view, calendar sync UI, explanation display
- **Weeks 8–10:** Push notifications, deep linking, home screen widgets (iOS + Android), background sync
- **Weeks 11–12:** App store submissions, crash reporting (Sentry), performance profiling

### Non-Negotiables
- Voice capture works **offline** (on-device Whisper tiny)
- First scheduled task within **90 seconds** of app open
- Cold start under **1.5 seconds**

### Definition of Done
Approved on both stores · crash-free rate > 99.5% · core flow completable in under 90 seconds

---

## Machine Learning

**Owner:** ML Engineer (1 IC, supported by Backend for infra)

### P1 Philosophy
P1 is **not a learning system yet** — it's a well-designed heuristic system with learning hooks in place. Real personalization kicks in at ~14 days of per-user data.

### Deliverables
- **Weeks 1–3:** Feature schema, training data collection plan, cold-start scheduling heuristic (rule-based with population priors), evaluation harness
- **Weeks 4–7:** v0 scheduling model — hybrid rules + LightGBM on simulated + alpha data. Explanation generation (template + LLM polish via Claude Haiku or GPT-4o-mini)
- **Weeks 8–10:** Online feedback capture (accept/reject/modify), per-user feature store, drift monitoring
- **Weeks 11–12:** Beta evaluation targeting ≥50% accepted-schedule rate on real users

### Scheduling Signals (ordered by weight in P1)
1. Due date and explicit priority
2. Calendar availability
3. Time-of-day productivity prior (bootstrapped from typical knowledge-worker curves, personalized after 2 weeks)
4. Mood and energy state at capture
5. Task difficulty estimate (user-entered, model-adjusted)

### Definition of Done
Model serving live · explanation quality ≥4/5 subjective rating from 50 beta users · retraining pipeline runs weekly

---

## DevOps / Agent Infrastructure

**Owner:** DevOps Engineer (1 IC)

### Deliverables
- **Weeks 1–2:** CI/CD (GitHub Actions), staging + prod environments (GCP or AWS), IaC (Terraform), secrets management
- **Weeks 3–5:** Kubernetes cluster, service mesh, logging (OpenTelemetry + Grafana Loki), metrics (Prometheus), error tracking (Sentry)
- **Weeks 6–8:** MCP server deployment + auth layer, rate limiting, DDoS protection (Cloudflare)
- **Weeks 9–12:** Production cutover, on-call runbooks, SLO dashboards, cost monitoring (target under $15k/mo at 10k MAU)

### Definition of Done
SLO dashboards live · on-call rotation operational · incident response drill completed · cost under target

---

## Cross-Functional: Privacy & Compliance

Co-owned by **PM + Backend Lead** (no dedicated role in P1).

- GDPR and CCPA baseline: consent, export, erasure
- EU AI Act Article 50 transparency notices (enforceable in 2026 for high-risk AI)
- On-device processing of mood data where feasible
- No behavioral data sold or shared — codified in ToS

---

## Week-by-Week Milestone Summary

| Week | Theme | Major milestone |
|---|---|---|
| 1–2 | Foundation | Flows finalized, infra provisioned, design system v1 |
| 3–4 | Scaffolding | Auth + API + mobile shell live |
| 5–6 | Capture loop | Voice/text task capture + mood check-in working |
| 7–8 | Schedule engine | v0 model + calendar sync + explanations shipped |
| 9 | Alpha | 200 internal + friendly users onboarded |
| 10 | MCP + integrations | LockIn callable from Claude + ChatGPT |
| 11 | Polish + stores | App store submissions, P0 bugs only |
| 12 | Beta launch | 1,000 users, metrics dashboard live |

---

## P1 Exit Criteria (all must be true to ship)

- ≥1,000 weekly active users in beta
- Accepted-schedule rate ≥ 50%
- D7 retention ≥ 30% (category benchmark: ~8–15%)
- MCP endpoint verified in Claude, ChatGPT, and Gemini
- p95 API latency < 200ms
- Crash-free rate > 99.5%
- Qualitative signal from ≥50 user interviews: *"this is meaningfully different from Motion or Reclaim"*

---

## What P1 Explicitly Does NOT Include
Gamification · 5-tier productivity classification · team features · Outlook sync · wearable integration · analytics dashboard · voice-based conversation (only voice capture) · habit tracking · web app.

All of the above live in P2 or P3. Do not let scope creep pull them into P1.

---
*Next review: Week 6 scope check-in. Any feature adding more than 1 week of work against this spec requires explicit PM approval and a corresponding cut.*
