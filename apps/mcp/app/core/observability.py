"""OpenTelemetry + Sentry wiring for the MCP server.

Mirrors apps/api/app/core/observability.py but drops the SQLAlchemy/Redis
instrumentations the MCP server doesn't use. Both exporters are opt-in via
empty env vars (no-op when unset).
"""

from __future__ import annotations

import sentry_sdk
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import settings

_configured = False


def configure_observability() -> None:
    """Idempotent. Call once at process start before any HTTP traffic."""
    global _configured
    if _configured:
        return

    _configure_sentry()
    _configure_otel()

    _configured = True


def _configure_sentry() -> None:
    if not settings.SENTRY_DSN_MCP:
        return
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN_MCP,
        release=settings.GIT_SHA,
        environment=settings.ENV,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
    )


def _configure_otel() -> None:
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

    HTTPXClientInstrumentor().instrument()
