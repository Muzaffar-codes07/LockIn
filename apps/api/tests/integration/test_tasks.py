"""Integration tests for the /v1/tasks endpoints.

These exercise the full slice spine: JWT auth -> DB write -> event publish.
The DB is the `lockin_test` database; Redis is an in-memory fake.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import fakeredis.aioredis
from httpx import AsyncClient
from jose import jwt  # type: ignore[import-untyped]
from lockin_events import STREAM_TASKS

from app.core.config import settings


# The default subject is a realistic Google OAuth `sub` (a numeric-ish
# string, not a UUID). The /v1/tasks route maps it through `user_uuid()`,
# so any stable string works as a subject here.
def _bearer(subject: str = "google-sub-117234567890") -> str:
    token = jwt.encode(
        {
            "user_id": subject,
            "email": "muzaffar@example.com",
            "providers": ["google"],
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALG,
    )
    return f"Bearer {token}"


async def test_create_task_requires_auth(db_client: AsyncClient) -> None:
    res = await db_client.post("/v1/tasks", json={"title": "no auth"})
    assert res.status_code == 401


async def test_create_task_rejects_empty_title(db_client: AsyncClient) -> None:
    res = await db_client.post(
        "/v1/tasks",
        headers={"Authorization": _bearer()},
        json={"title": ""},
    )
    assert res.status_code == 422


async def test_create_task_returns_201_with_the_task(db_client: AsyncClient) -> None:
    res = await db_client.post(
        "/v1/tasks",
        headers={"Authorization": _bearer()},
        json={"title": "Finish the spec doc"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "Finish the spec doc"
    assert body["source"] == "keyboard"
    assert "id" in body and "created_at" in body


async def test_create_task_emits_task_created_event(
    db_client: AsyncClient,
    fake_redis: fakeredis.aioredis.FakeRedis,
) -> None:
    await db_client.post(
        "/v1/tasks",
        headers={"Authorization": _bearer()},
        json={"title": "Emit an event"},
    )
    entries = await fake_redis.xrange(STREAM_TASKS)
    assert len(entries) == 1
    _entry_id, fields = entries[0]
    event = json.loads(fields["data"])
    assert event["event_type"] == "task.created"
    assert event["event_version"] == 1
    assert event["payload"]["title"] == "Emit an event"


async def test_list_tasks_returns_user_tasks_newest_first(db_client: AsyncClient) -> None:
    headers = {"Authorization": _bearer()}
    await db_client.post("/v1/tasks", headers=headers, json={"title": "first"})
    await db_client.post("/v1/tasks", headers=headers, json={"title": "second"})

    # Each POST is a separate transaction, so the two rows get distinct
    # `created_at` values; newest-first ordering is therefore deterministic.
    res = await db_client.get("/v1/tasks", headers=headers)
    assert res.status_code == 200
    titles = [t["title"] for t in res.json()]
    assert titles == ["second", "first"]


async def test_list_tasks_isolates_by_user(db_client: AsyncClient) -> None:
    await db_client.post(
        "/v1/tasks",
        headers={"Authorization": _bearer("user-a")},
        json={"title": "owned by A"},
    )
    res = await db_client.get(
        "/v1/tasks",
        headers={"Authorization": _bearer("user-b")},
    )
    assert res.status_code == 200
    assert res.json() == []


async def test_delete_task_is_idempotent(db_client: AsyncClient) -> None:
    headers = {"Authorization": _bearer()}
    created = await db_client.post("/v1/tasks", headers=headers, json={"title": "doomed"})
    task_id = created.json()["id"]

    first = await db_client.delete(f"/v1/tasks/{task_id}", headers=headers)
    assert first.status_code == 204

    # Deleting again is still 204 — desired end state already holds.
    second = await db_client.delete(f"/v1/tasks/{task_id}", headers=headers)
    assert second.status_code == 204

    remaining = await db_client.get("/v1/tasks", headers=headers)
    assert remaining.json() == []
