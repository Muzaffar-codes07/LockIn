# LockIn — Technical Roadmap
### Principal Engineer / Tech Lead View · April 2026
**Companion to:** PRD v2.1 · P1 Spec (Role-Based) · Competitive Re-Cut
**Horizon:** 12 months · P1 (Months 1–3) · P2 (Months 4–8) · P3 (Months 9–12)

---

## Engineering Principles (Apply to Every Phase)

1. **Build for P3 from P1, but don't ship P3 in P1.** Every P1 decision should be forward-compatible — schemas, event contracts, API shapes — but the surface area stays minimal.
2. **MCP is a first-class service, not an adapter.** The MCP server is peer to Capture, Scheduler, and Agent. Retrofitting later costs 10x.
3. **The behavior graph is the product.** Every schema choice optimizes for capturing and querying longitudinal user signals — not for rendering a screen today.
4. **Explainability is a system property.** The scheduler must emit structured reasoning alongside every decision, not generate post-hoc justifications.
5. **Degrade gracefully.** ML offline → heuristics serve. Whisper down → text fallback. Calendar API rate-limited → cache serves last-known-good.

---

# Phase 1 — Architecture & Foundation (Months 1–3)

**Mission:** Ship a responsive web MVP that closes the full user loop — capture → mood check → schedule with explanation → learn — and exposes the MCP endpoint to external agents.

**Success gate:** 1,000 beta users · ≥50% accepted-schedule rate · W1 retention ≥45% desktop / ≥35% mobile browser · MCP verified in Claude + ChatGPT + Gemini · p95 API <200ms · Lighthouse ≥90.

## 1.1 Architecture & Data Flow

### Service Topology

Four services behind a single API gateway, communicating via Redis Streams and Temporal workflows.

```
┌──────────────────────────────────────────────────────────────┐
│  Next.js App (Vercel)                                         │
│  - Responsive UI · Cmd+K capture · mood widget · schedule view│
└───────────────┬──────────────────────────────────────────────┘
                │  HTTPS · JWT session
                ▼
┌──────────────────────────────────────────────────────────────┐
│  API Gateway (FastAPI)                                        │
│  - Auth · rate limit · request routing                        │
└──┬────────┬────────┬────────┬──────────────────────────────────┘
   │        │        │        │
   ▼        ▼        ▼        ▼
┌──────┐ ┌────────┐ ┌───────┐ ┌──────────┐
│Capt. │ │Schedul.│ │Agent  │ │MCP Server│
│Svc   │ │Svc     │ │Svc    │ │          │
└──┬───┘ └───┬────┘ └───┬───┘ └────┬─────┘
   │         │          │          │
   └─────────┴──────────┴──────────┘
             │
   ┌─────────┴─────────────────────────┐
   ▼         ▼              ▼           ▼
┌──────┐ ┌────────┐  ┌────────────┐ ┌──────┐
│Postgres│ │Timescale│ │Redis       │ │Temporal│
│(core) │ │(events) │ │(cache+bus) │ │(flows)│
└──────┘ └────────┘  └────────────┘ └──────┘
```

### Design Patterns

- **Event-sourced behavior graph.** Every user action emits an immutable event to Redis Streams; Capture Service persists it to TimescaleDB for analytics and Postgres for transactional state. This is the only way to retroactively add ML features without losing historical data.
- **CQRS-lite.** Write-heavy paths (task capture, mood log) bypass the main Postgres ORM and write to Redis + TimescaleDB; read-heavy paths (today's schedule, explanation) hit Postgres. Keeps capture fast even at 10k concurrent users.
- **Saga via Temporal** for multi-step agent actions (reschedule → update Google Calendar → notify user → log outcome). A naive implementation of this as chained API calls is the #1 cause of inconsistent state in agentic systems.
- **Ports-and-adapters at the LLM boundary.** The explanation service depends on an interface, not on Claude or OpenAI. Switching providers or A/B-testing models is a config change, not a refactor.
- **Idempotent everything.** Every mutation API accepts a client-generated `idempotency_key`. Cheap insurance against retry storms.

### Key Data Flows

**Task capture → scheduled slot (happy path, target <3 seconds):**
1. Frontend emits `POST /tasks` with idempotency key
2. API gateway authenticates, routes to Capture Service
3. Capture Service writes `task.created` event to Redis Stream + persists to Postgres
4. Scheduler Service consumes event, queries calendar availability (cached in Redis), pulls user priors from feature store
5. LightGBM inference produces candidate slot + confidence score
6. Explanation Service pulls the feature vector, calls Claude Haiku with a templated prompt, caches the result
7. Scheduled slot + explanation returned to frontend via WebSocket push (already open from app load)

**MCP tool invocation (Claude calls `add_task`):**
1. Claude's MCP client calls our MCP server with OAuth 2.1 bearer token
2. MCP server validates token, translates tool call to internal API request
3. Identical to step 2 onwards above — the MCP path reuses the same services. This is the whole point.

## 1.2 Milestones & Tasks

### Weeks 1–2 — Foundations
- [ ] Monorepo setup (Turborepo or Nx); `apps/web`, `apps/api`, `apps/mcp`, `packages/shared-types`
- [ ] CI/CD pipeline (GitHub Actions → Vercel for web, GCP/AWS for backend)
- [ ] Terraform modules for VPC, Postgres (Cloud SQL), Redis, Kubernetes cluster
- [ ] Observability baseline: OpenTelemetry SDK, Sentry, Grafana dashboards with RUM
- [ ] Secret management (Google Secret Manager or AWS Secrets Manager)
- [ ] Auth: NextAuth + OAuth 2.1 (Google, Apple, Microsoft) + Passkey registration
- [ ] Design system package (`packages/ui`) with Tailwind tokens, base components
- [ ] Event schema v1 (tasks, mood, energy, schedule, explanation) — versioned from day one

### Weeks 3–4 — Scaffolding
- [ ] Postgres schemas with Alembic migrations (users, tasks, schedule_slots, mood_logs, energy_logs, explanations)
- [ ] TimescaleDB hypertables for time-series events
- [ ] Redis Streams topics + consumer groups configured
- [ ] API gateway (FastAPI) with JWT middleware, request ID propagation, rate limiting
- [ ] Google Calendar OAuth flow + initial read-only sync
- [ ] Frontend shell: routing, layout (responsive sidebar → bottom-tab), auth pages, empty states

### Weeks 5–6 — Capture Loop
- [ ] Task capture UI: Cmd+K command palette, slash commands, click-to-add, voice via MediaRecorder
- [ ] Backend voice pipeline: audio upload → cloud Whisper → structured task extraction via LLM
- [ ] Mood/energy widget (persistent in header): two-click interaction, optimistic UI, retry on fail
- [ ] Browser Notification API integration with deferred permission ask (after first scheduled task)
- [ ] Event instrumentation: every capture emits structured telemetry to analytics pipeline

### Weeks 7–8 — Scheduling Engine
- [ ] Cold-start scheduling heuristic (rule-based with population priors for knowledge workers)
- [ ] LightGBM v0 model trained on synthetic + alpha data
- [ ] Model serving: containerized FastAPI + gRPC for low-latency inference
- [ ] Feature store (Feast or homegrown on Postgres) for per-user signals
- [ ] Explanation Service: template + Claude Haiku polish, response caching in Redis
- [ ] Google Calendar bidirectional sync with conflict resolution
- [ ] **DECISION GATE — Week 8:** service worker stretch goal (ship or defer to P2)

### Weeks 9–10 — Agent + MCP
- [ ] Temporal workflows for agent actions (reschedule, accept, reject, modify)
- [ ] MCP server implementation exposing: `get_schedule`, `add_task`, `log_mood`, `explain_next_action`
- [ ] OAuth 2.1 device flow for MCP authentication
- [ ] Validation harness: automated test suite that invokes each MCP tool from Claude Desktop, ChatGPT, Gemini
- [ ] Alpha launch: 200 internal and friendly users

### Weeks 11–12 — Polish & Beta
- [ ] Performance tuning: Lighthouse 90+, Core Web Vitals all green, p95 <200ms
- [ ] Cross-browser QA (Chrome, Safari, Firefox, Edge — last two versions)
- [ ] Accessibility audit: WCAG 2.2 AA
- [ ] Landing page (SSR, SEO-optimized), Product Hunt assets
- [ ] Privacy tooling: data export (JSON + PDF), account erasure flow
- [ ] Incident response runbooks + on-call rotation
- [ ] Beta launch: 1,000 users, live metrics dashboard, feedback ops

## 1.3 Potential Roadblocks

| Risk | Severity | Mitigation |
|---|---|---|
| **MCP protocol spec drift** — The standard is young and evolving; a breaking change mid-P1 could require rework. | High | Abstract the MCP surface behind an internal interface; pin to a known-good spec version; track weekly. |
| **Google Calendar rate limits** — At 1,000 beta users with bidirectional sync, we'll approach the free tier limit quickly. | High | Request quota increase in Week 1 (takes 2–4 weeks to approve); implement exponential backoff and per-user sync throttling; cache aggressively. |
| **LLM explanation latency** — Claude Haiku at p99 can exceed 2s; users perceive anything >1s as "slow." | Medium | Cache explanations by feature-vector hash; pre-generate common patterns; show schedule immediately and stream the explanation. |
| **Cold-start ML quality** — First-week users get generic priors; 50% accepted-schedule rate is aggressive without personalization. | High | Invest heavily in population-prior heuristics; display confidence scores; fall back to user-modifiable drafts rather than committed decisions. |
| **Notification permission deny rate** — Browsers are hostile to permission requests; deny rates of 60%+ are common. | Medium | Request permission only after value is demonstrated (first accepted schedule); offer email/calendar-invite fallback nudges. |
| **OAuth refresh token management** — Multiple providers, different refresh semantics, edge cases around revocation. | Medium | Use a mature library (Auth.js); build a token-health dashboard from Week 3; assume 5% of tokens will silently expire monthly. |
| **Whisper cost scaling** — Voice at 10k MAU at even 2 captures/day is nontrivial. | Low | Cap free-tier voice at N captures/day; batch transcription; evaluate Deepgram as cheaper alternative in Week 6. |
| **Behavioral event volume** — TimescaleDB at 10k MAU × ~100 events/day = ~30M events/year. Fine for P1, architecture choice for P2. | Low | Partition by month from day one; plan cold-tier archival (S3 Parquet) for P2. |
| **Temporal operational overhead** — Adds real complexity for a team of 8. | Medium | Use Temporal Cloud rather than self-hosting in P1; revisit self-host in P2 when team grows. |
| **Tech-debt compounding** — Shipping fast in 12 weeks guarantees debt. | High | Budget 20% of each sprint for debt paydown starting Week 7; maintain a visible debt ledger. |

---

# Phase 2 — The Agent (Months 4–8)

**Mission:** Transform LockIn from a reactive scheduler into a proactive agent. Auto-reschedule, draft focus blocks, triage low-value meetings. Ship the browser extension. Harden the platform for scale.

**Success gate:** W4 retention ≥25% · accepted-schedule rate ≥70% · free→premium conversion ≥3% · service worker + Web Push live · Outlook sync shipped · first team pilots running.

## 2.1 Architecture & Data Flow

### What Changes

- **Per-user ML models** replace shared population priors. Per-user feature store becomes mandatory; training pipeline runs weekly.
- **Agent Decision Service** becomes its own component. Handles the meta-question: "should LockIn act autonomously, ask permission, or defer?" This is the hardest engineering problem in P2.
- **PWA layer** adds service worker, Web Push, install prompt, offline-first caching of today's schedule.
- **Browser extension** (Chrome + Firefox) ships as a thin client that reuses the existing API — no new backend.
- **Outlook sync** adds a second calendar adapter behind the existing ports-and-adapters calendar abstraction.
- **Team mode** introduces a tenancy layer: orgs → teams → users. Row-level security in Postgres becomes non-negotiable.

### Agent Decision Service — The Hard Part

The trust budget between user and agent is earned, not given. Every autonomous action has three possible confidence bands:

- **High confidence → act + notify.** ("I moved your 2pm to Thursday because your Wednesday is overloaded and you've rejected 4 Wednesday meetings this month.")
- **Medium confidence → propose with one-click accept.** ("Tuesday afternoon has three skippable meetings. Want me to decline them?")
- **Low confidence → surface but don't act.** ("You seem drained — light week?")

This is a classifier, not a threshold. Train it on explicit accept/reject signals from P1 + P2 data.

### Design Patterns Added in P2

- **Row-level security (RLS) in Postgres** for team-mode data isolation. Painful to retrofit; cheap to add when the tenancy layer first lands.
- **Feature flags as a platform primitive** (LaunchDarkly or OpenFeature). Every new agent behavior ships dark first, rolls out by cohort.
- **Offline-first state sync** via IndexedDB + service worker. Changes captured offline reconcile on next sync.
- **Event replay for ML training.** The event-sourced design from P1 pays its first big dividend — retraining on historical data requires no schema archaeology.

## 2.2 Milestones & Tasks

### Months 4–5
- [ ] Per-user feature store + weekly retraining pipeline (MLflow for experiment tracking)
- [ ] Agent Decision Service scaffold: rules-based v0, evolve to ML in Month 6
- [ ] Auto-reschedule workflow (Temporal saga): detect conflict → propose or act → notify → learn
- [ ] Service worker + Web Push → mood reminders fire with tab closed
- [ ] PWA manifest + install prompt → users can pin LockIn to home screen
- [ ] Outlook sync via Microsoft Graph API (reuses calendar adapter interface)

### Months 6–7
- [ ] Focus block drafting: scan next 48h, propose 2–3 deep-work windows
- [ ] Meeting triage: heuristic + LLM scoring for meeting-value prediction
- [ ] Browser extension (Chrome first, Firefox second): floating capture button, context-aware suggestions
- [ ] Team mode alpha: orgs, teams, RLS-protected Postgres queries, shared OOO
- [ ] Admin console for team owners (basic: invite, remove, view usage)

### Month 8
- [ ] Stripe integration for premium and team tiers
- [ ] SOC 2 Type II prep: policies, evidence collection, annual audit kickoff
- [ ] Load testing at 50k MAU equivalent
- [ ] P2 retention cohort analysis → go/no-go for native mobile in P3

## 2.3 Potential Roadblocks

| Risk | Severity | Mitigation |
|---|---|---|
| **Agent trust collapse from one bad action** — Moving a real meeting incorrectly burns the user permanently. | Critical | Every autonomous action must be reversible within 7 days; undo is one click from the notification; log all agent decisions for debugging. |
| **ML model drift at per-user level** — Without drift monitoring, a user's model silently degrades and they churn quietly. | High | Per-user drift metrics; auto-flag models with declining accepted-schedule rates; fallback to population priors when drift exceeds threshold. |
| **Outlook sync complexity** — Microsoft Graph API has different semantics for recurring events and meeting responses; edge cases proliferate. | High | Abstract calendar behavior at the port boundary; build a shared conformance test suite applied to both Google and Microsoft adapters. |
| **Service worker deployment risk** — SW caching bugs can serve stale app versions to users, sometimes for weeks. | Medium | Use `updateViaCache: 'none'`; implement skipWaiting + clientsClaim correctly; version every asset; maintain a "nuke the cache" emergency endpoint. |
| **RLS retrofit in team mode** — Adding tenancy to an existing Postgres schema is historically where projects break. | High | Add `tenant_id` columns and RLS policies at the schema level the day team mode lands; test with explicit negative queries (verify isolation). |
| **Temporal workflow versioning** — Long-running workflows and code changes don't mix well. | Medium | Use Temporal's versioning primitives from the first saga; never deploy breaking workflow changes without a migration path. |
| **Browser extension review delays** — Chrome Web Store review can take 1–4 weeks; Firefox is faster. | Low | Submit early, submit often; ship behind feature flag; have Firefox as fallback launch. |
| **Cost growth from ML inference** — Per-user models + LLM polish can escalate faster than revenue. | Medium | Budget per-user inference cost as a first-class metric; set per-tier inference quotas; evaluate self-hosted small models for explanation in Month 7. |

---

# Phase 3 — The Compound + Native Mobile (Months 9–12)

**Mission:** Ship native mobile (iOS + Android). Compound the behavioral data advantage into proprietary insights and habit formation. Earn the moat before a funded competitor targets us.

**Success gate:** Native mobile in both stores with ≥4.5 rating · D30 retention ≥15% · behavioral insights module live · 10k+ premium subscribers · Series A readiness.

## 3.1 Architecture & Data Flow

### What Changes

- **Native mobile clients (Flutter)** reuse the same backend API; no new services. On-device cache via Isar/Drift. On-device Whisper tiny for offline voice.
- **Insights engine** — a new service that runs scheduled behavioral analyses per user: best-hours clustering, mood-productivity correlation, anomaly detection for pattern shifts.
- **Gamification service** (opt-in): streaks, focus badges, weekly recap. Isolated so it never contaminates the core scheduling path.
- **Wearable integration** via HealthKit (iOS) and Health Connect (Android). Heart rate variability and sleep score become additional energy signals.
- **Third-party integrations** (Slack, Notion, Linear) via each platform's respective APIs. Where available, prefer their MCP servers over custom adapters.

### Design Patterns Added in P3

- **Offline-first on mobile** with last-write-wins plus vector-clock conflict resolution for task edits.
- **Background sync** for mood capture — even if the user never opens the app, the watch logs energy.
- **Federated insight computation** — certain expensive insights compute on-device from cached events, not on the server, for both privacy and cost.

## 3.2 Milestones & Tasks

### Months 9–10 — Native Mobile
- [ ] Flutter project scaffold sharing design tokens with web (via `packages/ui` where practical)
- [ ] Auth parity with web (OAuth + Passkeys via platform-native APIs)
- [ ] Core flows on mobile: capture (including on-device voice), mood widget, schedule view, explanation
- [ ] Push notifications via FCM + APNs
- [ ] Home screen widgets (iOS + Android) — glanceable "next up"
- [ ] Background sync worker for offline capture
- [ ] App store submissions (expect 1–3 weeks of review iteration)

### Month 11 — Compound
- [ ] Insights engine: daily batch jobs producing per-user analyses
- [ ] Behavioral insights UI: weekly recap, pattern discovery, confidence-scored observations
- [ ] Gamification service (opt-in): streaks, focus badges, weekly challenges
- [ ] HealthKit + Health Connect integration: HRV and sleep as additional scheduling signals
- [ ] Slack, Notion, Linear integrations (prefer official MCPs where they exist)

### Month 12 — Scale & Series A
- [ ] SOC 2 Type II audit completion
- [ ] Multi-region deployment (US-East + EU-West) — GDPR data residency
- [ ] Team and enterprise tier feature completeness (SSO, audit logs, admin analytics)
- [ ] Series A readiness package: metrics dashboard, cohort analysis, technical due diligence doc

## 3.3 Potential Roadblocks

| Risk | Severity | Mitigation |
|---|---|---|
| **Mobile parity gap** — Users expect web and mobile to behave identically; small divergences create "it's broken on mobile" support load. | High | Define parity as an explicit contract with automated cross-platform tests; flag divergences in CI. |
| **On-device model size for voice** — Whisper tiny is ~40MB; app size concerns on Android especially. | Medium | Lazy-download model on first voice use with clear UX; fall back to cloud when space-constrained. |
| **Wearable data privacy surface** — HealthKit/Health Connect adds sensitive data; EU AI Act scrutiny increases. | High | On-device processing of wearable signals where possible; explicit opt-in; wearable data never leaves device without explicit user action. |
| **Gamification backfiring** — Streaks create anxiety; badges can feel infantilizing for executives. | Medium | Opt-in only; persona-aware defaults (off by default for the Burnout-Averse Operator persona); measure whether gamification-on cohorts retain better than gamification-off (if not, rip it out). |
| **Third-party integration breakage** — Slack, Notion, Linear APIs change often; each break is a support incident. | Medium | Monitor integration health as a first-class SLO; degrade gracefully (show "sync paused" rather than broken state). |
| **Series A diligence blockers** — Missing SOC 2, poor test coverage, or weak incident runbooks can tank a raise. | High | Treat P3 as audit prep; engage SOC 2 vendor by Month 9; aim for 80%+ test coverage on critical paths. |
| **App store rejection for mood tracking** — Apple reviewers sometimes flag wellness-adjacent features. | Medium | Review guidelines carefully; frame as "productivity" not "health"; have a plan B (remove mood from store listing, keep in product) if rejected. |

---

# Cross-Cutting Concerns (All Phases)

## Security Posture

- **Threat model updated quarterly.** STRIDE framework; focus on auth, MCP abuse, data exfiltration via calendar integrations.
- **Pen tests:** quarterly from P1; bug bounty from P2.
- **Secrets hygiene:** no secrets in code, ever; rotate all API keys quarterly; use short-lived tokens for service-to-service auth.
- **Dependency scanning** (Dependabot + Snyk) on every PR; high-severity CVEs block merge.

## Observability SLOs

| Metric | P1 Target | P2 Target | P3 Target |
|---|---|---|---|
| API availability | 99.9% | 99.95% | 99.99% |
| API p95 latency | 200ms | 150ms | 100ms |
| Client error rate | <0.5% | <0.3% | <0.2% |
| Accepted-schedule rate | 50% | 70% | 75% |
| MCP endpoint uptime | 99.9% | 99.95% | 99.99% |

## Tech Debt Management

- Visible debt ledger (GitHub Project or Linear) with severity and estimated paydown.
- 20% of sprint capacity reserved for debt from Week 7 of P1 onwards.
- No more than 3 "critical" items in the ledger at any time; exceeding triggers a debt sprint.

## Compliance Milestones

- **P1:** GDPR, CCPA, EU AI Act Article 50 compliance at beta launch.
- **P2:** SOC 2 Type II audit in progress; bug bounty live.
- **P3:** SOC 2 Type II certified; ISO 27001 kickoff.

---

## Final Notes from the Tech Lead Chair

The two decisions that determine whether this roadmap ships are both architectural, both happen in the first month, and both have nothing to do with features:

**1. The event schema.** Every ML feature we'll want in 2027 is downstream of the events we log in Week 3. Invest a full week in getting this right. Versioned from day one. Forward-compatible field additions only. Breaking changes require a migration path.

**2. The MCP abstraction layer.** If the MCP tools are built as direct wrappers over internal APIs, every API change breaks external agents. Build the MCP layer as a stable contract, and version it independently of the internal API.

Get those two right and the rest is tractable. Get either wrong and P2 is a rewrite.

---
*Review cadence: monthly at phase boundaries, quarterly for full roadmap re-ratification.*
