# Current Slice — Vertical Slice 0: Auth + Task Capture Spine

**Status:** Active
**Owner:** [assigned engineer]
**Est. duration:** 3–5 days

## The Goal

Build the smallest possible end-to-end loop that proves the architecture works. Nothing else until this ships.

**User story:**
> As a user, I can sign in with Google, open a Cmd+K command palette, type a task title, press Enter, and see it appear in a simple list. The task persists across page refreshes.

That's it. No calendar sync. No mood widget. No ML. No MCP. No scheduling.

## Why This Slice First

If this works end-to-end, everything else layers onto the same spine:
- Auth works → we can add per-user data
- Cmd+K works → we have the primary input surface for all future features
- API + DB write works → we can add event sourcing, then mood, then calendar
- Event emitted → we prove the event-sourced architecture from day one

If this DOESN'T work, nothing else matters. This is the foundation test.

## What "Done" Looks Like

- [ ] `npm run dev` starts the web app at localhost:3000
- [ ] `docker compose up` starts Postgres + Redis locally
- [ ] `python -m uvicorn app.main:app --reload` starts the API at localhost:8000
- [ ] User visits localhost:3000, clicks "Sign in with Google", completes OAuth
- [ ] User sees empty dashboard with a prompt: "Press Cmd+K to add a task"
- [ ] User presses Cmd+K, command palette opens, types "Finish spec doc", presses Enter
- [ ] Task appears in a list below the palette
- [ ] User refreshes the page; task is still there
- [ ] In the database: `SELECT * FROM tasks;` shows the task with correct `user_id`
- [ ] In Redis Streams: `XRANGE events:tasks - +` shows a `task.created` event
- [ ] An integration test covers the full flow

## Architecture Constraints for This Slice

**DO:**
- Write the event schema for `task.created` in `packages/events/` FIRST, before any code
- Use server actions or tRPC (pick one, document it) for the API call — no separate fetch plumbing yet
- Write the task to Postgres AND emit to Redis Streams (dual write is fine for slice 0; we'll add outbox pattern in slice 2)
- Set up shared TypeScript types between web and API via `packages/shared-types/`

**DO NOT:**
- Build generic abstractions "for later" — write the concrete code, refactor when we have three use cases
- Add a mood widget, calendar sync, or any other feature
- Skip the event emission "because we're not reading it yet" — the event is the point

## Stretch Goal (only if truly ahead of schedule)

Add a `DELETE /tasks/:id` endpoint and a delete button. Emits `task.deleted` event. This forces us to think about idempotency in the simplest possible context.

## What's Next (slice 1 preview)

After this ships, slice 1 is: **Google Calendar read-only sync.** The user connects their calendar and sees today's events alongside the task list. No scheduling logic yet — just read-only display.

---
*Update this file when the slice ships. Archive previous slices in `docs/slices/`.*
