"""Task creation and listing.

`create` performs a dual write: the row is committed to Postgres, then a
`task.created` event is published to the `events:tasks` Redis Stream. This is
a deliberate Slice-0 simplification — the transactional outbox pattern lands
in a later slice. The publish happens only after a successful commit.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from lockin_events import STREAM_TASKS, TaskCreated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.task import Task
from app.events.publisher import EventPublisher


class TaskService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        publisher: EventPublisher,
        *,
        user_id: UUID,
        title: str,
        source: str,
    ) -> Task:
        task = Task(id=uuid4(), user_id=user_id, title=title, source=source)
        self._session.add(task)
        await self._session.commit()
        await self._session.refresh(task)

        event = TaskCreated.model_validate(
            {
                "event_id": str(uuid4()),
                "event_type": "task.created",
                "event_version": 1,
                "user_id": str(user_id),
                "tenant_id": None,
                "occurred_at": task.created_at.isoformat(),
                "client_idempotency_key": None,
                "source": "web",
                "payload": {
                    "task_id": str(task.id),
                    "title": task.title,
                    "source": task.source,
                },
            }
        )
        await publisher.publish(STREAM_TASKS, event)
        return task

    async def list_for_user(self, user_id: UUID) -> list[Task]:
        result = await self._session.execute(
            select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())
