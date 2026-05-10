# LockIn MCP - Production Dockerfile
# Derived from apps/api/Dockerfile (do not regenerate apps/api version).
#
# Build:  docker build -t lockin-mcp -f apps/mcp/Dockerfile .
# Run:    docker run -p 8081:8081 -e MCP_TRANSPORT=sse --env-file .env lockin-mcp

# ---------------------------------------------------------------------------
# Stage 1: builder
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

COPY apps/mcp/pyproject.toml apps/mcp/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY apps/mcp/app ./app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---------------------------------------------------------------------------
# Stage 2: runtime
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

RUN groupadd --system --gid 1001 lockin \
    && useradd --system --uid 1001 --gid lockin --no-create-home lockin

# No libpq5 here — MCP server has no Postgres driver.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder --chown=lockin:lockin /opt/venv /opt/venv

WORKDIR /app
COPY --from=builder --chown=lockin:lockin /app/app ./app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MCP_TRANSPORT=sse

USER lockin

EXPOSE 8081

# Stdio mode runs interactively over stdin/stdout; SSE mode binds 8081.
# Switch via MCP_TRANSPORT env var.
CMD ["python", "-m", "app.main"]
