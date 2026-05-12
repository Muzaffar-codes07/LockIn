# @lockin/events

Source of truth for the LockIn event schema.

## Source of truth

- [`src/schema.ts`](src/schema.ts) (Zod) is the **only** place to add or modify events.
- `dist/json-schema/*.json` (emitted) and `python/lockin_events/generated.py` (codegen) are derived artifacts. **Do not edit by hand.**

## Regenerate after any schema change

```bash
pnpm -F @lockin/events gen
```

Three steps run in order:

1. `pnpm gen:json-schema` — `tsx scripts/emit-json-schema.ts` writes one JSON Schema per event into `dist/json-schema/`.
2. `pnpm gen:python` — `uvx datamodel-codegen` writes the merged pydantic models into `python/lockin_events/generated.py`.
3. `pnpm build` — `tsc -p tsconfig.json` emits the TS `dist/`.

The PowerShell wrapper (`scripts/gen-python.ps1`) is used on Windows; CI runners use the POSIX twin (`scripts/gen-python.sh`).

## Versioning rule

- **Additive** optional fields → no version bump.
- **Removal**, rename, or semantic change → bump `event_version` and document a migration path.
- Breaking changes require Md sign-off — the behavior graph forks otherwise.

## Streams

| Stream             | Carries                                                                      |
| ------------------ | ---------------------------------------------------------------------------- |
| `events:tasks`     | `task.created`, `task.modified`, `task.completed`                            |
| `events:signals`   | `mood.logged`, `energy.logged`                                               |
| `events:schedule`  | `task.scheduled`, `task.accepted`, `task.rejected`                           |
| `events:agent`     | `schedule.explained`                                                         |

See [`src/streams.ts`](src/streams.ts) / [`python/lockin_events/streams.py`](python/lockin_events/streams.py) for the canonical mapping.

## Fixtures

`fixtures/<event_type>.json` holds one minimal-but-valid example per event type. The TS and Python tests round-trip every fixture through their respective parsers to keep the two language sides in lockstep.
