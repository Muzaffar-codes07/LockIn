"""Liveness endpoint. No DB or Redis check — that's a separate /readyz later."""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
