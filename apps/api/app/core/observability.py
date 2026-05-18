"""Wire OpenTelemetry + Sentry once at FastAPI startup.

Traces go to Grafana Cloud's OTLP HTTP endpoint
(``GRAFANA_CLOUD_OTLP_ENDPOINT``) authenticated via a single Basic header
(base64 of ``instance_id:token``) supplied as ``GRAFANA_CLOUD_OTLP_AUTH``.
Sentry receives exception telemetry via ``SENTRY_DSN_API``.

Both exporters are **opt-in** — empty env vars mean the relevant SDK
becomes a no-op. This keeps unit tests and local dev free of network noise
without per-environment branching elsewhere in the code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sentry_sdk
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.core.config import settings

if TYPE_CHECKING:
    from fastapi import FastAPI


_configured = False


def configure_observability(app: FastAPI) -> None:
    """Idempotent. Safe to call multiple times in the same process."""
    global _configured
    if _configured:
        return

    _configure_sentry()
    _configure_otel(app)

    _configured = True


def _configure_sentry() -> None:
    if not settings.SENTRY_DSN_API:
        return
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN_API,
        release=settings.GIT_SHA,
        environment=settings.ENV,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        integrations=[
            FastApiIntegration(),
            StarletteIntegration(),
        ],
    )


def _configure_otel(app: FastAPI) -> None:
    if not settings.GRAFANA_CLOUD_OTLP_ENDPOINT:
        return

    resource = Resource.create(
        {
            "service.name": settings.APP_NAME,
            "service.version": settings.APP_VERSION,
            "deployment.environment": settings.ENV,
        }
    )
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=f"{settings.GRAFANA_CLOUD_OTLP_ENDPOINT.rstrip('/')}/v1/traces",
        headers={"Authorization": f"Basic {settings.GRAFANA_CLOUD_OTLP_AUTH}"},
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    RedisInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()
