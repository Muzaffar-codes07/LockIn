# LockIn API - Production Dockerfile
# Multi-stage build using uv for fast, deterministic, layer-cacheable installs.
#
# Build:  docker build -t lockin-api -f apps/api/Dockerfile .
# Run:    docker run -p 8000:8000 --env-file .env lockin-api

# ---------------------------------------------------------------------------
# Stage 1: builder - install dependencies into a clean venv
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

# Install uv from the official distroless image (smallest, fastest pull)
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

# uv environment knobs:
# - UV_COMPILE_BYTECODE=1     compile .pyc on install (faster cold start)
# - UV_LINK_MODE=copy         avoid hardlink warnings in Docker layers
# - UV_PYTHON_DOWNLOADS=never use the system Python; do not download a separate one
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

# Install dependencies first (cached layer when only source code changes)
# Mounting the lockfile and pyproject.toml as build secrets keeps the cache stable.
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Now copy the actual source and install the project itself
COPY apps/api/app ./app
COPY apps/api/alembic ./alembic
COPY apps/api/alembic.ini ./alembic.ini

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---------------------------------------------------------------------------
# Stage 2: runtime - minimal image with just the venv and the app
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

# Create a non-root user for the app
RUN groupadd --system --gid 1001 lockin \
    && useradd --system --uid 1001 --gid lockin --no-create-home lockin

# Install runtime system dependencies (libpq for psycopg, ca-certificates for HTTPS)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder --chown=lockin:lockin /opt/venv /opt/venv

# Copy the application code
WORKDIR /app
COPY --from=builder --chown=lockin:lockin /app/app ./app
COPY --from=builder --chown=lockin:lockin /app/alembic ./alembic
COPY --from=builder --chown=lockin:lockin /app/alembic.ini ./alembic.ini

# Make the venv the default Python environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER lockin

EXPOSE 8000

# Health check that hits the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

# Run with uvicorn directly (use gunicorn + uvicorn workers in K8s if you need
# multiple worker processes per pod; otherwise let K8s scale pod count instead).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
