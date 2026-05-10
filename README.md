# LockIn Bootstrap — How to Start Building with Claude Code

This directory is a **minimal starting shell** for the LockIn project. It contains the context files Claude Code needs to be immediately useful, plus a bootstrap script to scaffold the real monorepo.

## What's in Here

```
.
├── CLAUDE.md                    ← Persistent context (Claude Code reads this every session)
├── bootstrap.sh                 ← One-time scaffolding script
├── docs/
│   ├── CURRENT_SLICE.md         ← What we're building RIGHT NOW (only this, nothing else)
│   ├── PRD.md                   ← Copy your PRD here
│   ├── P1_Spec.md               ← Copy your P1 spec here
│   ├── Technical_Roadmap.md     ← Copy your roadmap here
│   └── Competitive_ReCut.md     ← Copy your competitive doc here
└── packages/
    └── events/
        └── schema.ts            ← THE event schema. Read it before touching anything.
```

## The 15-Minute Start

```bash
# 1. Clone or copy this directory to where you want the project to live
cp -r lockin-bootstrap ~/projects/lockin && cd ~/projects/lockin

# 2. Copy your actual project docs into docs/
#    (PRD_v2.md, P1_Spec_RoleBased.md, Technical_Roadmap.md, Competitive_ReCut.md)

# 3. Run the bootstrap
chmod +x bootstrap.sh && ./bootstrap.sh

# 4. Fill in .env.local (Google OAuth credentials at minimum)

# 5. Start local infrastructure
docker compose -f infra/docker/docker-compose.yml up -d

# 6. Open Claude Code
claude
```

## The First Claude Code Session

Once Claude Code is open in the repo, start with this **exact** prompt:

> Read `CLAUDE.md` and `docs/CURRENT_SLICE.md`. Then propose a plan for implementing the current slice. Do not write any code yet — show me the plan first, including file-by-file structure, the order you'd build things, and any decisions you need me to make.

**Why this prompt works:**

1. It forces Claude Code to load persistent context before acting
2. "Do not write code yet" prevents the classic AI failure of generating 2,000 lines that miss the point
3. "Show me the plan first" gives you a chance to course-correct before commits happen
4. Asking for "decisions you need me to make" surfaces the small choices that matter (Drizzle vs Prisma, NextAuth v4 vs v5, etc.)

## The Discipline That Makes This Work

**One slice at a time.** When the current slice ships:
1. Archive `CURRENT_SLICE.md` to `docs/slices/00_auth_task_spine.md`
2. Write a new `CURRENT_SLICE.md` for the next slice
3. Start a fresh Claude Code session

**Do not work on multiple slices in parallel.** The reason Claude Code gets confused is context overload. Keep the focus narrow and the docs current.

## Recommended Slice Sequence (P1)

```
Slice 0: Auth + Task Capture Spine          (3–5 days)  ← CURRENT
Slice 1: Google Calendar Read-Only Sync     (3–4 days)
Slice 2: Event Sourcing + Outbox Pattern    (2–3 days)
Slice 3: Mood/Energy Widget + Events        (3–4 days)
Slice 4: Scheduling Service (heuristic v0)  (5–7 days)
Slice 5: Explanation Service (LLM polish)   (3–4 days)
Slice 6: MCP Server (Claude/ChatGPT/Gemini) (5–7 days)
Slice 7: Landing page + Onboarding polish   (3–4 days)
Slice 8: Beta launch prep                   (3–5 days)
```

That's 8 slices over ~12 weeks, which matches the P1 roadmap with realistic slack for debugging, refactors, and user research.

## What Claude Code is Good At

- Writing boilerplate (Next.js routes, FastAPI endpoints, Pydantic models, Tailwind components)
- Translating between type systems (TypeScript ↔ Python via shared contracts)
- Maintaining consistency across a codebase once patterns are set
- Running tests, linting, and debugging
- Refactoring when you have a clear goal

## What Claude Code is NOT Good At

- Making product decisions (keep those in docs, not in prompts)
- Inventing architecture from scratch (that's why `CLAUDE.md` is opinionated)
- Knowing when to stop (you have to enforce scope; that's what `CURRENT_SLICE.md` is for)
- Remembering previous sessions (CLAUDE.md solves this; chat history doesn't persist)

## The One Rule That Matters

**Update `CLAUDE.md` and `CURRENT_SLICE.md` as the project evolves.** Stale docs are the #1 failure mode when using Claude Code on a long project. Treat them as living specs, not archive material.

---
*This bootstrap was generated in April 2026. Verify dependency versions before you run.*
