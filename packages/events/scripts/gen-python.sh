#!/usr/bin/env bash
# Regenerate lockin_events.generated from the merged JSON Schema.
set -euo pipefail

PKG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCHEMA_FILE="$PKG_ROOT/dist/json-schema/_all.json"
OUT_FILE="$PKG_ROOT/python/lockin_events/generated.py"

if [ ! -f "$SCHEMA_FILE" ]; then
  echo "Merged JSON schema not found at $SCHEMA_FILE. Run 'pnpm gen:json-schema' first." >&2
  exit 1
fi

uvx --from 'datamodel-code-generator>=0.26' datamodel-codegen \
  --input "$SCHEMA_FILE" \
  --input-file-type jsonschema \
  --output "$OUT_FILE" \
  --output-model-type pydantic_v2.BaseModel \
  --target-python-version 3.12 \
  --use-double-quotes \
  --disable-timestamp \
  --use-schema-description

echo "Generated $OUT_FILE"
