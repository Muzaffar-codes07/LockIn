# ADR-0001: Adopt ADR workflow for architectural decisions

Date: 2026-05-11
Status: Accepted

## Context

LockIn has multiple source-of-truth documents (CLAUDE.md, PRD, Roadmap, Design Spec). Graphify audits surfaced duplication and drift between them. Architectural reasoning was scattered across commit messages, chat sessions, and inline comments — invisible to future Claude Code sessions and hard for humans to retrieve.

## Decision

Adopt lightweight ADRs in `docs/adr/`. Each substantive architectural decision gets a numbered markdown file with Context, Decision, Consequences. ADRs are immutable post-acceptance; changes are made by writing a superseding ADR.

## Consequences

- Future Claude Code sessions can read `docs/adr/` to understand why structural decisions were made.
- Graphify extracts ADRs as nodes, so the audit graph will start showing decisions linked to the code they constrain.
- One more file to write per decision — but only for genuine decisions, not routine work.
- Reversing a decision now requires explicit ADR work, which is friction-by-design.
