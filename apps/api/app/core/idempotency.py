"""Idempotency-key extraction. Storage backend lands per slice."""

from typing import Annotated

from fastapi import Header

IdempotencyKey = Annotated[
    str | None,
    Header(alias="Idempotency-Key", description="Client-generated UUID for safe retries."),
]
