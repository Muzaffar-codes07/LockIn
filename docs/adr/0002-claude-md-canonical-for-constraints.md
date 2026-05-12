# ADR-0002: CLAUDE.md is canonical for constraint-bearing rules

Date: 2026-05-11
Status: Accepted

## Context

Graphify audit found "Architectural Non-Negotiables" in the PRD duplicated "Locked Tech Stack" in CLAUDE.md, and "Product Principles" in PRD duplicated "Non-Negotiable Principles" in CLAUDE.md. Drift between the two was a real maintenance hazard. Additionally, CLAUDE.md auto-loads into every Claude Code session while the PRD is read selectively, so constraints in CLAUDE.md are more reliably seen by the agent.

## Decision

CLAUDE.md is the canonical home for any rule that constrains how code should be written. The PRD retains product framing, strategic positioning, and rationale, but defers to CLAUDE.md via pointers for constraint-bearing content.

## Consequences

- Constraints live in the file the agent always reads — fewer missed rules at code-generation time.
- PRD shrinks; it remains a strategic document, not a rulebook.
- When a new constraint is decided, it goes in CLAUDE.md, not the PRD.
- Graphify audits should no longer surface tech-stack or principle-level duplication between CLAUDE.md and the PRD.
