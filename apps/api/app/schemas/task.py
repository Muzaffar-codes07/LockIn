"""Request/response contracts for the /v1/tasks endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

TaskSource = Literal["keyboard", "click", "voice", "mcp"]


class TaskCreate(BaseModel):
    """Body of `POST /v1/tasks`."""

    title: str = Field(min_length=1, max_length=500)
    source: TaskSource = "keyboard"


class TaskRead(BaseModel):
    """A task as returned by the API. Built from the ORM row."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    source: str
    created_at: datetime
