# LockIn MCP Server

Model Context Protocol server exposing LockIn tools to Claude, ChatGPT, and Gemini.

## Local development

```pwsh
uv venv
uv sync --extra dev
$env:MCP_TRANSPORT = "stdio"
uv run python -m app.main
```

For production-style local testing over HTTP/SSE:

```pwsh
$env:MCP_TRANSPORT = "sse"
uv run python -m app.main
```

## Tests

```pwsh
uv run pytest
```

## Docker build (from repo root)

```pwsh
docker build -t lockin-mcp -f apps/mcp/Dockerfile .
```

See [the design spec](../../docs/superpowers/specs/2026-05-10-production-restructure-design.md) for the architecture rationale.
