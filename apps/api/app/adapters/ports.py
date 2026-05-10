"""Adapter port definitions. Structural typing only — no inheritance."""

from datetime import date
from typing import Any, Protocol


class LLMPort(Protocol):
    async def complete(self, prompt: str, *, max_tokens: int = 1024) -> str: ...


class CalendarPort(Protocol):
    async def list_events(self, user_id: str, day: date) -> list[dict[str, Any]]: ...


class VoiceTranscriberPort(Protocol):
    async def transcribe(self, audio: bytes) -> str: ...
