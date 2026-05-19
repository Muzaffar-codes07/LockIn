"""Unit tests for the OAuth-subject → UUID mapping."""

from __future__ import annotations

from uuid import UUID

from app.core.identity import user_uuid


def test_user_uuid_is_stable_for_same_subject() -> None:
    assert user_uuid("117234567890") == user_uuid("117234567890")


def test_user_uuid_differs_per_subject() -> None:
    assert user_uuid("subject-a") != user_uuid("subject-b")


def test_user_uuid_returns_a_uuid() -> None:
    assert isinstance(user_uuid("117234567890"), UUID)
