# Decision: Frontend data layer + user-identity mapping (Slice 0)

**Date:** 2026-05-18
**Status:** Accepted

## Context

`CURRENT_SLICE.md` instructed "use server actions or tRPC". The real backend
is FastAPI (Python); tRPC is TypeScript-only and Server Actions run only in
the Next.js runtime — neither calls FastAPI directly. Separately, auth is
JWT-strategy with no `users` table: identity is Google's `sub` (a numeric
string), but the event schema types `user_id` as `UUID`.

## Decision

1. **Data layer:** React Query (TanStack Query, already locked in `CLAUDE.md`)
   on the client, calling a thin Next.js BFF route handler (`/api/tasks`) that
   forwards the HttpOnly session-token cookie as a Bearer token to FastAPI.
2. **Identity:** `app/core/identity.py:user_uuid()` maps an OAuth subject to a
   deterministic `uuid5` UUID, used as the key for every per-user row and event.

## Consequences

- No CORS surface — the browser only talks to same-origin Next.js routes.
- React Query's mutation primitives are ready for the Week 5 optimistic mood UI.
- The `_USER_NAMESPACE` constant in `identity.py` must never change — doing so
  re-keys every user. A real `users` table (P2 team mode) can adopt the same
  derived UUID as its primary key with no data migration.
