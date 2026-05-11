#!/usr/bin/env pwsh
# Regenerate lockin_events.generated from the merged JSON Schema.
$ErrorActionPreference = "Stop"

$pkgRoot = Resolve-Path "$PSScriptRoot/.."
$schemaFile = Join-Path $pkgRoot "dist/json-schema/_all.json"
$outFile = Join-Path $pkgRoot "python/lockin_events/generated.py"

if (-not (Test-Path $schemaFile)) {
    throw "Merged JSON schema not found at $schemaFile. Run 'pnpm gen:json-schema' first."
}

uvx --from "datamodel-code-generator>=0.26" datamodel-codegen `
    --input $schemaFile `
    --input-file-type jsonschema `
    --output $outFile `
    --output-model-type pydantic_v2.BaseModel `
    --target-python-version 3.12 `
    --use-double-quotes `
    --disable-timestamp `
    --use-schema-description

Write-Host "Generated $outFile"
