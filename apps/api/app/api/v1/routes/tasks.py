"""`/v1/tasks` — create and list a user's captured tasks."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.v1.deps import DbSession, EventPublisherDep
from app.core.auth import CurrentUserDep
from app.core.identity import user_uuid
from app.schemas.task import TaskCreate, TaskRead
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    user: CurrentUserDep,
    session: DbSession,
    publisher: EventPublisherDep,
) -> TaskRead:
    service = TaskService(session)
    task = await service.create(
        publisher,
        user_id=user_uuid(user.user_id),
        title=body.title,
        source=body.source,
    )
    return TaskRead.model_validate(task)


@router.get("", response_model=list[TaskRead])
async def list_tasks(user: CurrentUserDep, session: DbSession) -> list[TaskRead]:
    service = TaskService(session)
    tasks = await service.list_for_user(user_uuid(user.user_id))
    return [TaskRead.model_validate(task) for task in tasks]


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    user: CurrentUserDep,
    session: DbSession,
) -> Response:
    service = TaskService(session)
    # Idempotent: 204 whether or not the row existed.
    await service.delete(user_id=user_uuid(user.user_id), task_id=task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
