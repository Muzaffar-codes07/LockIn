"""JWT validation for the API.

NextAuth v5 issues HS256-signed JWTs using the shared ``AUTH_SECRET`` env var.
The API verifies the same secret. Future non-Google providers (Apple, MS in
the Week 5 polish window) all flow through the same signed-JWT path.
"""

from __future__ import annotations

from typing import Annotated, Any, cast

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt  # type: ignore[import-untyped]
from pydantic import BaseModel

from app.core.config import settings


class CurrentUser(BaseModel):
    user_id: str
    email: str | None = None
    providers: list[str] = []


def _decode(token: str) -> dict[str, Any]:
    try:
        return cast(
            dict[str, Any],
            jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALG],
                options={"verify_aud": False},
            ),
        )
    except JWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token") from exc


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer")
    token = authorization.split(" ", 1)[1]
    claims = _decode(token)
    user_id = claims.get("user_id") or claims.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "token missing user_id")
    return CurrentUser(
        user_id=user_id,
        email=claims.get("email"),
        providers=list(claims.get("providers", [])),
    )


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
