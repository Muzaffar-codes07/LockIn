"""Integration tests for /v1/__debug__/* routes."""

from httpx import AsyncClient


async def test_force_500_raises_in_non_prod(client: AsyncClient) -> None:
    res = await client.get("/v1/__debug__/force_500")
    assert res.status_code == 500


async def test_debug_ping_responds_in_non_prod(client: AsyncClient) -> None:
    res = await client.get("/v1/__debug__/ping")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
