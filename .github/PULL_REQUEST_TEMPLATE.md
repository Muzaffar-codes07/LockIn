## Summary

-

## Slice

> Which slice in [`docs/CURRENT_SLICE.md`](../docs/CURRENT_SLICE.md) does this advance?

## Checks

- [ ] Lint, typecheck, tests pass locally
- [ ] No new dependencies introduced without an ADR
- [ ] No secrets in diff (grep)
- [ ] If event schema changed: `pnpm -F @lockin/events gen` was re-run and committed
- [ ] If infra changed: `terraform plan` output reviewed in CI
- [ ] If a Week 1–2 deliverable was touched: matching acceptance criterion in `docs/handoffs/week-1-2.md` is still green
