"""MCP-side adapter ports. Structural typing only."""
from typing import Any, Protocol


class APIClientPort(Protocol):
    async def get_tasks(self, user_id: str) -> list[dict[str, Any]]: ...
