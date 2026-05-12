"""Shared pytest fixtures."""

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    # raise_app_exceptions=False makes uncaught exceptions surface as 500
    # responses, matching production ASGI servers. Without it, ASGITransport
    # re-raises into the test, which is the wrong contract for /v1/__debug__/
    # exception-path tests.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
