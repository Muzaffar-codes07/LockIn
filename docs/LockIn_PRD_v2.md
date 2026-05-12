# LockIn — Product Requirements Document
### The Mood-and-Energy-Aware Productivity Agent

**Version:** 2.0
**Date:** April 2026
**Supersedes:** PRD v1.0 (November 2025)
**Classification:** Internal · Draft
**Companion docs:** Scope Memo v2 · P1 Spec (Role-Based) · Competitive Re-Cut

---

## 1. Executive Summary

LockIn is a **personal productivity agent** that schedules your day based on how you actually work — when you focus best, how mood affects your output, what energy state you're in — and explains every decision it makes.

It is designed from day one to be both a **standalone product** and a **tool callable by other AI agents** (Claude, ChatGPT, Gemini) via the Model Context Protocol.

**Durable moat:** Longitudinal behavioral data that nobody else captures. Mood, energy, completion patterns, and context gathered over weeks and months. General-purpose agents cannot replicate this without explicit tracking infrastructure. Competing schedulers (Motion, Reclaim, Saner) ignore mood and energy entirely. (The P1 wedge product is what captures this data; see [`glossary.md`](glossary.md).)

**Built for 2030 standards:** agent-native, memory-first, MCP-compatible, voice-default, privacy-preserving by design.

---

## 2. Vision & Thesis

### The 2030 Bet

By 2030, three things are table stakes for any serious productivity product:

1. **Agents act without being asked** — proactive beats reactive.
2. **AI has persistent memory** of how individuals work — context beats context-window.
3. **Productivity tools interoperate** via open protocols (MCP and successors) — composability beats silos.

Any product shipped in 2026 as a "dashboard with AI features" is obsolete by 2028. LockIn is shipped as a 2030 product in 2026.

### LockIn's Durable Moat

**Longitudinal behavioral data.** When *you* focus. What *your* mood costs you. How *your* energy decays across a week. This dataset compounds with every capture and cannot be purchased, scraped, or inferred by a general-purpose agent.

### What We Are Not

- Not a task manager (Todoist is)
- Not a project management tool (Linear, Asana are)
- Not an all-in-one workspace (Notion is)
- Not a generic AI assistant (ChatGPT, Claude are)

LockIn is the **productivity-agent layer** that makes all of those tools more effective by knowing who the user actually is.

---

## 3. Target Users

Three personas, simplified from v1.

### The Calendar-Chaos Knowledge Worker
- **Who:** 28–45, PM/engineer/designer, hybrid or remote
- **Pain:** Too many tasks, constant context switching, schedule anxiety
- **Goal:** Someone else deciding what to work on next, without being bossy about it

### The Rhythm-Seeker
- **Who:** 22–35, individual contributor, freelancer, solo founder
- **Pain:** Inconsistent output, productivity plateau, difficulty building focus habits
- **Goal:** A system that adapts to their actual patterns rather than forcing a generic template

### The Burnout-Averse Operator
- **Who:** 30–50, founder, executive, high-performer
- **Pain:** Sustainability, energy management, pace control
- **Goal:** Productivity that doesn't kill them

### Explicitly Deprecated
The v1 "Peak Performer / High Achiever / Steady Contributor / Struggling Professional / Burnout Risk" classification is removed. It doesn't correlate with user value, risks shaming users, and buries the product in dashboard thinking.

---

## 4. Core Product

### Product Principles

The constraint-bearing form of these principles — the rules that govern implementation — lives in [`CLAUDE.md`](../CLAUDE.md) under **"Non-Negotiable Principles"**. This section captures the *strategic framing* for each: what we believe about users, the market, and where defensibility comes from.

1. **Agent-Native.** Productivity tools that report state lose to tools that take action. LockIn's strategic stance is doing the work, not showing the work.

2. **Memory-First.** Longitudinal behavioral data is the durable advantage. General-purpose agents cannot replicate it without capture infrastructure. The graph compounds; the schedule is a side effect.

3. **Explainable.** Opacity is the fastest path to churn in an AI-saturated market. Users tolerate AI suggestions only when the "why" is visible and grounded in their own behavior.

4. **Composable (MCP).** In 2026, the productivity surface is the agent layer. A LockIn that isn't callable from Claude, ChatGPT, and Gemini is invisible to the actual workflow.

5. **Privacy-Preserving by Default.** Behavioral data is high-trust material. Selling it is product-suicide in the EU and a slow trust-erosion in the US. On-device where feasible, export on demand, never sold.

### Core User Loop

1. **Capture** a task (voice or text, under 10 seconds)
2. **Check in** on mood and energy (two taps, under 5 seconds, max 3×/day)
3. **LockIn schedules** with an inline explanation
4. **User accepts, modifies, or rejects**
5. **LockIn learns** from every decision

### Shippable Features by Phase

#### P1 (Months 1–3) — The Wedge
- Voice and text task capture
- 3-tap mood and energy check-in
- Google Calendar bidirectional sync
- AI scheduling with natural-language explanations
- MCP endpoint (Claude, ChatGPT, Gemini callable)
- iOS and Android apps (Flutter)

#### P2 (Months 4–8) — The Agent
- Auto-reschedule when plans change
- Drafted focus blocks
- Low-value meeting triage ("this looks skippable — decline?")
- Outlook sync
- Cross-device continuity
- Early team mode (2–5 people)
- Web app

#### P3 (Months 9–12) — The Compound
- Behavioral insights (after 30 days of data)
- Opt-in gamification (streaks, focus badges)
- Wearable signals (Apple Watch, Pixel Watch, Oura)
- Habit formation module
- Third-party integrations (Slack, Notion, Linear)

### Explicitly Cut or Deferred from v1

| Feature | Disposition | Reason |
|---|---|---|
| 5-tier productivity classification | **Cut** | Doesn't drive value, risks shaming users |
| Gamification as first-class system | **Deferred to P3, opt-in** | Signals "toy" not "tool" in 2026 |
| Comprehensive analytics dashboard | **Deferred to P3** | Dashboard thinking loses in the agent era |
| Team leaderboards | **Cut indefinitely** | Wrong incentive model |
| Corporate wellness angle | **Cut** | Different product, different buyer |
| Voice-first marketing | **Cut** | Voice is a feature, not a position |

---

## 5. Technical Architecture

### Service Topology

Three major services, all agent-first:

1. **Capture Service** — Ingests tasks, mood, energy, and calendar events. Voice transcription via on-device Whisper with cloud fallback.
2. **Scheduler Service** — Produces schedules with explanations. Hybrid system: rule-based priors + LightGBM per-user model + LLM-generated natural-language explanations.
3. **Agent Service** — Exposes LockIn as MCP tools. Handles proactive actions: auto-reschedule, meeting triage, focus block drafting.

### Stack

The authoritative tech stack lives in [`CLAUDE.md`](../CLAUDE.md) under **"Tech Stack (Locked)"**. This section previously duplicated that content; it now defers to the canonical source to prevent drift. Deeper trade-off notes live in [`docs/LockIn_Technical_Roadmap.md`](LockIn_Technical_Roadmap.md).

### Architectural Non-Negotiables

The authoritative list of locked product and architectural principles lives in [`CLAUDE.md`](../CLAUDE.md) under **"Non-Negotiable Principles"**. That list covers agent-native action, memory-first behavior graph, explainability, MCP as a first-class service, graceful degradation, idempotency, on-device inference for mood/energy, voice and ambient capture as default input paths, and open data portability.

---

## 6. Machine Learning Strategy

### P1: Well-Designed Heuristics + Learning Hooks

P1 is not a learning system yet. It is a thoughtfully designed heuristic system with the infrastructure to become one.

- Cold-start uses population priors (typical knowledge-worker productivity curves)
- Per-user personalization kicks in after ~14 days of data
- LightGBM for scheduling decisions
- LLM polish for natural-language explanations (Claude Haiku preferred for cost and speed)

### P2: Personalized Models

- Per-user feature store
- Online learning from accept/reject/modify feedback
- Drift detection, weekly retraining
- Agent decision model for proactive actions (when to reschedule, when to ask vs. act)

### P3: Advanced Behavioral Models

- Sequence mining for behavioral workflows
- Burnout prediction (high-specificity, low-false-positive — false alarms kill trust)
- Anomaly detection for pattern shifts (travel, illness, major life events)

### Model Serving

- **Lightweight predictions** (next-task suggestion, difficulty estimate) — serverless (Cloud Run / Lambda)
- **Complex inference** (full schedule generation) — dedicated containers
- **Experiment tracking** — MLflow
- **A/B testing** — native framework from day one

---

## 7. Privacy, Security, Compliance

### Privacy Principles

- **Data minimization** — we collect only what improves scheduling
- **On-device processing** for mood/energy signals where feasible
- **Full export** (JSON + human-readable PDF) on request, within 24 hours
- **Full erasure** within 7 days of request
- **No sale of behavioral data**, codified in ToS

### Regulatory Readiness

| Regulation | Status | Target |
|---|---|---|
| GDPR (EU) | Required at launch | P1 ship |
| CCPA (California) | Required at launch | P1 ship |
| EU AI Act Article 50 (transparency) | Required 2026 | P1 ship |
| SOC 2 Type II | Year 1 target | Month 12 |
| ISO 27001 | Year 2 target | Month 24 |
| HIPAA | Not in scope | — |

### Security

- **Passkeys + OAuth 2.1** (primary auth), MFA (fallback)
- **TLS 1.3** in transit, **AES-256** at rest
- **E2E encryption** for mood/energy data specifically
- **Quarterly penetration tests** from P1
- **Bug bounty program** from P2

---

## 8. Go-to-Market

### Phase Gates

- **P1 beta (Month 3)** — Product Hunt launch, productivity influencer partnerships, ~1,000 beta users
- **P2 public (Month 8)** — App store featuring push, SEO content ("AI scheduler that understands mood"), paid acquisition with measured CAC caps
- **P3 scale (Month 12)** — Integration partnerships (Slack, Notion, Linear), team/enterprise pilots, EU launch then APAC

### Positioning Statement

> *"LockIn is the productivity agent that knows you. It learns your rhythms, respects your energy, and plans your day so you don't have to. Callable from any AI assistant. Built for how you actually work."*

### Channels (Prioritized)

1. **Content marketing (SEO)** — highest ROI for this category; own "AI scheduler mood energy" and "explainable productivity AI"
2. **Product Hunt + Show HN** — founder credibility and early evangelists
3. **Productivity creator partnerships** — YouTube, TikTok, X
4. **MCP ecosystem discovery** — Claude and ChatGPT users find us as a tool
5. **App Store Optimization** — keywords, screenshots, video
6. **Referral program** — from P2

---

## 9. Business Model

### Pricing

#### Free (the majority of users)
- Task capture, calendar sync, mood check-in
- Basic scheduling (no auto-reschedule)
- 30-day behavioral history
- MCP endpoint access

#### Premium — **$9.99/month** or **$89/year**
- Auto-reschedule and proactive agent actions
- Unlimited behavioral history and insights
- Focus-block drafting and meeting triage
- Multi-calendar support
- Wearable integration (P3+)
- Priority support

#### Teams — **$14.99/user/month** (P2+)
- Team focus-time coordination
- Shared OOO and energy visibility
- Admin controls

#### Enterprise — Custom (P3+)
- SSO, SOC 2, SLAs, dedicated support

### Unit Economics (Rebuilt from Ground Truth)

| Metric | Target | Category benchmark |
|---|---|---|
| Free → Premium conversion | 3% | 2.6% median |
| CAC (blended) | $18–22 | — |
| Premium monthly churn | <5% | 5–8% typical |
| Annualized churn (Y1) | 35% | 40–50% typical |
| LTV:CAC ratio | 3:1 minimum | — |

### Year 1 Revenue Projection (realistic)

- 50,000 free users (not the v1 target of 100k — too aggressive for an 8-person team)
- 1,500 premium conversions at 3%
- End-of-Y1 ARR: ~$150,000
- End-of-Y2 goal: 300k free, 12k premium, ~$1.2M ARR

---

## 10. Success Metrics

### Product Quality (Ground-Truth Benchmarks)

| Metric | P1 Target | Category benchmark |
|---|---|---|
| D1 retention | 45% | 17.1% |
| D7 retention | 30% | ~8% |
| D30 retention | 15% | 4.1% |
| Accepted-schedule rate | 50% (P1) → 70% (P2) | — |
| Time-to-first-schedule | under 90 sec | — |
| App store rating | 4.5+ | — |
| Crash-free rate | >99.5% | — |

### Engagement

- **DAU/MAU:** 40%+ (productivity app benchmark: ~20%)
- **Sessions per day:** 3–5
- **Session length:** 2–4 min (quick, not sticky — the anti-pattern in social apps is the pattern here)

### Business

- **Free → Premium conversion:** 3%+
- **Premium monthly churn:** under 5%
- **NPS:** 40+ (v1's 50 target was aspirational for a new-category product; 40 is realistic and still strong)

---

## 11. Risks & Mitigations

### Product Risk
- **Explanation fatigue** — users tune out AI reasoning over time. *Mitigation:* A/B test explanation prominence; make explanations dismissible after N accepts.
- **Mood tracking feels creepy** — privacy-conscious users balk. *Mitigation:* on-device inference, visible user control, clear value messaging.

### Market Risk
- **ChatGPT Agent eats our lunch** — users ask ChatGPT to plan their week. *Mitigation:* MCP-first strategy — be the memory layer ChatGPT calls, not the competitor.
- **Reclaim or Saner adds behavioral ML** — our feature becomes commodity. *Mitigation:* ship the moat fast; lean into voice-first + on-device + mood depth.
- **Apple ships mood tracking at WWDC 2026** — our signal layer gets commoditized. *Mitigation:* deeper behavioral model (not just mood), cross-platform, MCP.

### Technical Risk
- **ML model quality in cold-start** — bad first impressions kill retention. *Mitigation:* strong population-prior heuristics, honest confidence display, rapid feedback capture.
- **MCP protocol changes** — the standard is young. *Mitigation:* abstract the integration layer; track MCP spec weekly.

### Organizational Risk
- **Scope creep** — P1 blows past 3 months. *Mitigation:* this PRD explicitly enumerates what we are not building.
- **Team burnout on aggressive MVP** — 8 people shipping in 3 months is hard. *Mitigation:* 8 people is deliberately under-scoped for the stated goal; kill P1 features before people.

---

## 12. Team & Budget

### P1 Team (8 people)
- 1 Product Manager
- 1 Designer (UX + UI)
- 2 Mobile Engineers (Flutter)
- 2 Backend Engineers
- 1 ML Engineer
- 1 DevOps / Agent Infrastructure Engineer

### P2 Additions — Months 4–8 (+4)
- 1 Web Engineer
- 1 ML Engineer
- 1 Growth / Marketing Lead
- 1 QA Engineer

### P3 Additions — Months 9–12 (+3)
- 1 Data Engineer
- 1 Customer Success
- 1 Sales (Teams/Enterprise pilots)

### Year 1 Budget

| Line | Amount |
|---|---|
| Personnel (8→15 ramp) | $1.4M |
| Cloud + ML infrastructure | $200k |
| Tooling and SaaS | $60k |
| Marketing | $100k |
| Legal and compliance | $50k |
| **Total** | **$1.8M** |

### Funding Path

- **Seed raise:** $2.5M at P1 ship (Month 3)
- **Series A gate:** P2 retention data — if D30 retention ≥ 15% and accepted-schedule rate ≥ 60%, raise; otherwise iterate before raising

---

## 13. Open Questions

1. Do we ship an **Android-first** beta given Android's stronger adoption in emerging markets where the agentic AI shift is slower?
2. Is there an on-device behavioral model we can ship in P2 to harden the privacy moat?
3. When do we publicly commit to the **MCP thesis** vs. treat it as a private integration?
4. What's our position if **Apple ships mood tracking at WWDC 2026**?
5. What's the right team-mode pricing — per-seat or per-team-flat?
6. Do we invest in a **browser extension** in P2 for web-based workflow capture?

---

## 14. Document Control

**Version:** 2.0
**Date:** April 2026
**Supersedes:** PRD v1.0 (November 2025)
**Authors:** Product Team
**Companion docs:** Scope Memo v2 · P1 Spec (Role-Based) · Competitive Re-Cut

### Changes from v1

- Reframed from "productivity platform" to "productivity agent"
- Cut 5-tier productivity classification
- Deferred gamification, team features, advanced analytics
- Added MCP as first-class architectural requirement
- Rebuilt success metrics against ground-truth category benchmarks
- Shrunk team from 15 to 8 for P1; budget from $2–2.7M to $1.8M
- Added 2030 thesis; removed calendar-company history and generic ML benchmarks
- Competitive section updated for Clockwise shutdown, Motion repricing, Saner/Lindy emergence, agentic AI wave

### Approvals Required
- [ ] Product Leadership
- [ ] Engineering Leadership
- [ ] Design Leadership
- [ ] ML Leadership
- [ ] Legal & Compliance
- [ ] Executive Sponsor

### Next Review
Month 2 — mid-P1 scope check-in. Material changes to scope, budget, or timeline require re-ratification.

---
*End of PRD v2.*
