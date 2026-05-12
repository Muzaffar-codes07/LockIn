# Architectural Decision Records

ADRs document architectural decisions and their rationale. Each ADR is immutable once accepted; if a decision changes, write a new ADR that supersedes the old one and mark the old one's status as "Superseded by ADR-NNNN".

## Format

```
# ADR-NNNN: Short imperative title

Date: YYYY-MM-DD
Status: Proposed | Accepted | Superseded by ADR-NNNN | Deprecated

## Context
What's the situation that prompted this decision? Keep to 2-4
sentences. Reference graphify findings, performance data, or
specific code paths when relevant.

## Decision
What was decided. State it imperatively. One paragraph.

## Consequences
What changes because of this decision. Both positive and negative.
Bullet list, 3-6 items.
```

## Guidelines

- Keep each ADR under 200 words. If it's longer, the decision probably isn't crisp enough yet.
- ADRs are for decisions that *constrain future work*. Not for bug fixes, routine refactors, or exploratory discussions.
- Number ADRs sequentially: 0001, 0002, etc. Do not skip numbers.
- Filename pattern: `NNNN-kebab-case-title.md`
- Once committed, do not edit an ADR's substance. Only edit Status.

## When to write one

Good signals that a decision is ADR-worthy:
- Choosing between two viable technical approaches.
- Accepting a trade-off (e.g., "we'll do X knowing it costs Y").
- Establishing a pattern other code should follow.
- Reversing a previous decision.

Bad signals (do not write ADRs for these):
- "We fixed a bug."
- "We added a feature the spec already called for."
- "We discussed but didn't decide."
