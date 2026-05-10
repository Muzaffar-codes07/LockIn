# LockIn — Competitive Re-Cut
**April 2026 · Companion to PRD v2**

---

## What Changed Since PRD v1 (November 2025)

Three shifts invalidate the original competitive framing:

1. **Clockwise shut down in March 2026.** Reclaim absorbed most of their user base with a migration tool and a 100% price-match guarantee.
2. **Motion repriced** to $29/mo Pro AI ($19/mo annual) — not $34 as PRD v1 stated — and leaned harder into enterprise workflows with AI credits.
3. **The agent wave landed.** ChatGPT Agent, Gemini Personal Intelligence, Claude Cowork, and Siri's 2026 overhaul all ship features that overlap with LockIn's stated value prop.

**The competitive set is no longer "AI schedulers." It's "anything that can plan your day."**

---

## Direct Competitors (Same Product Category)

### Motion
- **What they are:** All-in-one task + calendar + project management, aggressive auto-scheduler
- **Strength:** Hands-off scheduling, strong for project-heavy workflows, native mobile
- **Weakness:** $29/mo with no free tier, "calendar anxiety" from over-reshuffling, steep learning curve, enterprise tilt alienates individuals
- **Where we beat them:** Mood and energy awareness, explainability, gentler control, real free tier
- **Where they beat us:** Project management depth, team coordination features

### Reclaim.ai
- **What they are:** Calendar defender, habits + focus time, layered onto Google/Outlook
- **Strength:** Genuine free tier, gentle rescheduling, mature product, Clockwise refugees
- **Weakness:** Basic task management, no mood or energy signal, no agentic action, no mobile app
- **Where we beat them:** Behavioral learning, proactive agent actions, mobile-first, explanation-first UI
- **Where they beat us:** Distribution, integration breadth, calendar-defense maturity

### Saner.ai *(new entrant — not in PRD v1)*
- **What they are:** Daily planning + AI prioritization + unified workspace at $8/mo
- **Strength:** Price, clean UX, native mobile, integrated inbox
- **Weakness:** No behavioral learning, no mood signals, thin ML layer, limited integration breadth
- **Where we beat them:** Longitudinal behavioral data, agent actions, explainability
- **Where they beat us:** Price, shipped product, time-in-market

### Lindy
- **What they are:** Personal AI assistant over SMS — email, calendar, routine tasks
- **Strength:** Text-message UX is novel, writing-style learning, low friction
- **Weakness:** Single modality, no productivity categorization, no visual schedule
- **Where we beat them:** Deeper productivity model, mobile-first visual UX, mood/energy signal
- **Where they beat us:** Setup simplicity, novelty factor

---

## Adjacent Threats (Different Category, Overlapping Value)

### ChatGPT Agent (OpenAI)
- **The threat:** Autonomous browser agent that books, drafts, researches. $200/mo Pro or Plus with limits.
- **Why it's a risk:** Users will ask ChatGPT "plan my week" and get a passable answer — even if it's worse than ours.
- **Why we still win:** Generic agents lack longitudinal behavioral data. They don't know your energy patterns. They don't log mood. They don't remember that last Thursday was draining.
- **Our counter-move:** Expose LockIn as an **MCP tool** ChatGPT Agent can call. Become the memory-and-scheduling layer behind the agent rather than competing head-on.

### Gemini Personal Intelligence (Google)
- **The threat:** Cross-app context from Gmail, Calendar, Photos, Search. Free. Default on Android.
- **Why it's a risk:** Deep integration, zero switching cost, massive distribution.
- **Why we still win:** Google optimizes for Google's engagement metrics, not for user wellbeing. Mood and energy are not in their model — and likely never will be, for privacy-optics reasons.
- **Our counter-move:** Deep Google Calendar integration via MCP; position as "the productivity soul Gemini lacks."

### Claude Cowork (Anthropic)
- **The threat:** Desktop agent that reads, edits, and creates files. Traction among non-coders.
- **Why it's a risk:** Overlap on file/doc workflow automation.
- **Why we still win:** Cowork is desktop-first and file-focused, not schedule-focused.
- **Our counter-move:** Be the calendar and productivity agent Cowork calls.

### Siri Overhaul + Microsoft Copilot Tasks
- Both expected H2 2026. Will subsume basic scheduling voice commands.
- **Our moat:** Depth of behavioral model, cross-platform coverage, no ecosystem lock-in.

---

## Legacy Players (On the Field, Not Our Fight)

- **Todoist, TickTick** — Task list excellence, no agent. **Complementary**, not competitive. Potential integration targets.
- **Notion, ClickUp** — Workspace tools, not schedulers. Integration opportunities.
- **Asana, Linear, Jira** — Team project management. Different buyer, different use case.
- **Calendly, Cal.com** — Booking links for external meetings. Orthogonal problem space.

---

## Positioning Matrix

| Capability | Motion | Reclaim | Saner | Lindy | ChatGPT Agent | **LockIn** |
|---|---|---|---|---|---|---|
| Mood/energy aware | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |
| Explainable scheduling | Partial | ✗ | ✗ | ✗ | ✗ | **✓** |
| Agent-native (takes action) | ✓ | Partial | Partial | ✓ | ✓ | **✓** |
| MCP-exposed | ✗ | ✗ | ✗ | ✗ | n/a | **✓** |
| Free tier | ✗ | ✓ | ✓ | ✗ | Partial | **✓** |
| On-device mood inference | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |
| Longitudinal behavior graph | Partial | ✗ | ✗ | ✗ | ✗ | **✓** |
| Mobile-first | ✓ | ✗ | ✓ | Partial | Partial | **✓** |

---

## The Wedge

LockIn wins by being the **only tool that models the user as a person over time**, not as a task list.

- Motion optimizes schedules.
- Reclaim protects time.
- Saner organizes the inbox.
- Agents execute commands.

**LockIn remembers that you're bad on Mondays, that the biweekly all-hands drains you, and that your best deep work is between 9:15 and 11:45 when the kids are at school.**

That dataset compounds with use. It cannot be bought or replicated by a general-purpose agent without the capture infrastructure. It is the moat.

---

## Threats to Watch in 2026

1. **Saner.ai raising capital and expanding scope** — closest product-market overlap, cheaper than us.
2. **Apple adding mood tracking to Health + Siri integration** — would commoditize our signal layer. WWDC 2026 is the event to watch.
3. **Reclaim adding ML-based personalized scheduling** — they have distribution. If they ship our core feature, the game fundamentally changes.
4. **A new entrant with $20M+ and the same thesis** — the market is hot enough that this is a *when*, not an *if*.

---

## How We Talk About Competitors Publicly

- **Never disparage.** The AI productivity space is small and reputations compound.
- **Position against categories, not products.** "The productivity agent that knows you" — not "better than Motion."
- **Acknowledge Motion and Reclaim as strong.** Then pivot to what's missing: the user themselves.
- **Treat the big-tech agents as distribution partners**, not rivals. MCP is the bridge.

---

## Strategic Implications for Product Roadmap

1. **Ship mood and energy capture in P1.** It's the unreplicated signal and the pitch.
2. **Ship MCP endpoint in P1.** The alternative — retrofitting later — gives competitors a year of lead time to become the default.
3. **Defer gamification indefinitely.** Habitica owns that frame and it signals "toy" not "tool" in 2026.
4. **Keep the free tier real.** Reclaim proved the category needs it; Motion is bleeding share by refusing.
5. **Price premium at $9.99, not higher.** Saner at $8 anchors the low end; we're worth a small premium but not 3x.

---
*Review monthly. Competitive landscape in this category is now moving quarter-over-quarter.*
