"""Integration tests for the WebAuthn registration endpoints.

These exercise endpoint shape, auth gating, and the in-process challenge
state machine. A full attestation-roundtrip test with synthetic key material
is out of scope for this slice — see ``apps/api/tests/e2e`` for the future
home of that test.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from jose import jwt  # type: ignore[import-untyped]

from app.api.v1.routes import webauthn as webauthn_route
from app.core.config import settings


def _bearer(user_id: str = "00000000-0000-4000-8000-000000000001") -> str:
    token = jwt.encode(
        {
            "user_id": user_id,
            "email": "muzaffar@example.com",
            "providers": ["google"],
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALG,
    )
    return f"Bearer {token}"


@pytest.fixture(autouse=True)
def _clear_challenge_state() -> None:
    webauthn_route._pending_challenges.clear()


async def test_options_requires_auth(client: AsyncClient) -> None:
    res = await client.post("/v1/webauthn/register/options")
    assert res.status_code == 401


async def test_verify_requires_auth(client: AsyncClient) -> None:
    res = await client.post("/v1/webauthn/register/verify", json={})
    assert res.status_code == 401


async def test_options_returns_expected_shape_and_stashes_challenge(
    client: AsyncClient,
) -> None:
    res = await client.post(
        "/v1/webauthn/register/options",
        headers={"Authorization": _bearer()},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["rp"] == {"id": settings.WEBAUTHN_RP_ID, "name": "LockIn"}
    assert "challenge" in body and isinstance(body["challenge"], str)
    assert any(p["alg"] == -7 for p in body["pubKeyCredParams"])  # ES256
    # Server-side state stashed for the same user_id used in the bearer
    assert "00000000-0000-4000-8000-000000000001" in webauthn_route._pending_challenges


async def test_verify_with_no_pending_challenge_returns_400(client: AsyncClient) -> None:
    res = await client.post(
        "/v1/webauthn/register/verify",
        headers={"Authorization": _bearer()},
        json={"credential": {"id": "abc"}},
    )
    assert res.status_code == 400
    assert "no pending" in res.json()["detail"]


async def test_verify_missing_credential_returns_400(client: AsyncClient) -> None:
    # Seed a pending challenge so we get past that gate
    webauthn_route._put_challenge("00000000-0000-4000-8000-000000000001", b"\x00" * 32)
    res = await client.post(
        "/v1/webauthn/register/verify",
        headers={"Authorization": _bearer()},
        json={},
    )
    assert res.status_code == 400
    assert "credential" in res.json()["detail"]


async def test_verify_invalid_attestation_returns_400(client: AsyncClient) -> None:
    # Seed a pending challenge then send a garbage credential payload —
    # verify_registration_response should fail and we should translate that
    # to a 400.
    webauthn_route._put_challenge("00000000-0000-4000-8000-000000000001", b"\x00" * 32)
    res = await client.post(
        "/v1/webauthn/register/verify",
        headers={"Authorization": _bearer()},
        json={
            "credential": {
                "id": "not-a-real-credential",
                "rawId": "not-a-real-credential",
                "type": "public-key",
                "response": {
                    "attestationObject": "garbage",
                    "clientDataJSON": "garbage",
                },
            }
        },
    )
    assert res.status_code == 400
    assert "attestation failed" in res.json()["detail"]
