"""Unit tests for app.core.auth — HS256 JWT validation used by /v1/me.

These tests are pure (no DB, no FastAPI client) — they exercise the
``get_current_user`` dependency callable directly with synthetic Authorization
headers.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from jose import jwt  # type: ignore[import-untyped]

from app.core.auth import CurrentUser, get_current_user
from app.core.config import settings


def _sign(claims: dict) -> str:
    return str(jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALG))


def test_missing_header_raises_401() -> None:
    with pytest.raises(HTTPException) as exc:
        get_current_user(authorization=None)
    assert exc.value.status_code == 401
    assert "missing bearer" in exc.value.detail


def test_non_bearer_scheme_raises_401() -> None:
    with pytest.raises(HTTPException) as exc:
        get_current_user(authorization="Basic abc")
    assert exc.value.status_code == 401


def test_invalid_signature_raises_401() -> None:
    bad = jwt.encode({"user_id": "u1"}, "different-secret", algorithm="HS256")
    with pytest.raises(HTTPException) as exc:
        get_current_user(authorization=f"Bearer {bad}")
    assert exc.value.status_code == 401
    assert "invalid token" in exc.value.detail


def test_missing_user_id_raises_401() -> None:
    token = _sign({"exp": datetime.now(UTC) + timedelta(minutes=5)})
    with pytest.raises(HTTPException) as exc:
        get_current_user(authorization=f"Bearer {token}")
    assert exc.value.status_code == 401
    assert "user_id" in exc.value.detail


def test_valid_token_returns_user() -> None:
    token = _sign(
        {
            "user_id": "00000000-0000-4000-8000-000000000001",
            "email": "muzaffar@example.com",
            "providers": ["google"],
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        }
    )
    user = get_current_user(authorization=f"Bearer {token}")
    assert isinstance(user, CurrentUser)
    assert user.user_id == "00000000-0000-4000-8000-000000000001"
    assert user.email == "muzaffar@example.com"
    assert user.providers == ["google"]


def test_falls_back_to_sub_when_user_id_absent() -> None:
    token = _sign(
        {
            "sub": "google-oauth2|abc",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        }
    )
    user = get_current_user(authorization=f"Bearer {token}")
    assert user.user_id == "google-oauth2|abc"
    assert user.providers == []
