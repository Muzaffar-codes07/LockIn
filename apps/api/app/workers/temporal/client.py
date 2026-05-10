"""Temporal client factory.

Targets Temporal Cloud in all non-local environments. TLS is enabled when
both TEMPORAL_TLS_CERT and TEMPORAL_TLS_KEY are present in env.
Local dev defaults to localhost:7233 with TLS off.
"""
from temporalio.client import Client
from temporalio.service import TLSConfig

from app.core.config import settings


async def get_temporal_client() -> Client:
    tls: TLSConfig | bool = False
    if settings.TEMPORAL_TLS_CERT and settings.TEMPORAL_TLS_KEY:
        tls = TLSConfig(
            client_cert=settings.TEMPORAL_TLS_CERT.encode(),
            client_private_key=settings.TEMPORAL_TLS_KEY.encode(),
        )
    return await Client.connect(
        settings.TEMPORAL_HOST,
        namespace=settings.TEMPORAL_NAMESPACE,
        tls=tls,
    )
