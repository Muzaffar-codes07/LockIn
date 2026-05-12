# Cloud + OAuth decisions for P1

**Date:** 2026-05-11
**Decided by:** Md
**Recorded for:** Week 1–2 Foundation slice

## Cloud

**Choice:** GCP.

**Rationale:**
- Vercel-adjacent latency for the web app (same network edge).
- First-class Cloud SQL Postgres 16 + TimescaleDB.
- Memorystore for Redis (Streams in P1, full feature set later).
- Team familiarity skews toward GCP IAM.

AWS deferred. Switching later means new Terraform modules, OIDC re-bootstrap, and a Memorystore→ElastiCache data migration — a Phase 2+ conversation.

## OAuth scope for P1 auth

**Choice:** Google only.

**Rationale:**
- Matches `CLAUDE.md` ("Google only in P1").
- Ships Week 1–2 on schedule. Adding Apple and Microsoft each adds ~1 day plus a separate review cycle.
- Apple + Microsoft are tracked for the Week 5 polish window.

## Implications encoded in this slice

- Terraform modules in `infra/terraform/modules/` target GCP only.
- GitHub Actions workflows reference `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_PROJECT_ID`, etc.
- `apps/web/src/auth.ts` (Task 9, deferred) wires only the Google provider.
- WebAuthn passkey is in scope regardless of OAuth provider count.

## Cost of reversal

- **Cloud swap to AWS:** ~5–7 days of rewrites at Week 1–2 cost; rises sharply once real data lands.
- **Add Apple/MS providers:** ~1 day each; clean additive change to NextAuth config + a callback URL per provider.
