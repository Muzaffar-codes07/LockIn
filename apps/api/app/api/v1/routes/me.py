"""`/v1/me` — returns the authenticated user from the bearer JWT.

The web app calls this when a non-Next.js client (MCP server, native app) needs
the same identity surface as `apps/web/src/app/api/me/route.ts`.
"""

from fastapi import APIRouter

from app.core.auth import CurrentUser, CurrentUserDep

router = APIRouter(tags=["me"])


@router.get("/me", response_model=CurrentUser)
async def me(user: CurrentUserDep) -> CurrentUser:
    return user
