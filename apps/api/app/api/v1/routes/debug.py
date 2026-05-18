"""Debug-only routes used to exercise observability wiring.

The forced-500 endpoint exists so the Week 1-2 handoff acceptance criterion
'Forced 500 in staging surfaces in Sentry + Grafana within 60s' is testable
end-to-end. The endpoint is gated to non-production environments so a
misclick can't paint the prod error rate red.
"""

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings

router = APIRouter(prefix="/__debug__", tags=["debug"], include_in_schema=False)


class ForcedFailure(Exception):
    """Raised by /v1/__debug__/force_500. Sentry captures this as a 500."""


@router.get("/force_500")
async def force_500() -> dict[str, str]:
    if settings.ENV == "production":
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    raise ForcedFailure(
        "forced 500 from /v1/__debug__/force_500 — verify Sentry issue + "
        "Grafana error-rate panel + Slack alert within 60s"
    )


@router.get("/ping")
async def ping() -> dict[str, str]:
    """Cheap baseline trace for verifying OTel pipeline without erroring."""
    if settings.ENV == "production":
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return {"status": "ok", "env": settings.ENV}
