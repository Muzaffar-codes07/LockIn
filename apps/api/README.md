# LockIn API

FastAPI gateway and core services for LockIn.

## Local development

```pwsh
uv venv
uv sync --extra dev
uv run uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/v1/health`

## Tests

```pwsh
uv run pytest
```

## Lint and types

```pwsh
uv run ruff check .
uv run ruff format .
uv run mypy app
```

## Docker build (from repo root)

```pwsh
docker build -t lockin-api -f apps/api/Dockerfile .
```

See [the design spec](../../docs/superpowers/specs/2026-05-10-production-restructure-design.md) for the architecture rationale.
