"""JWT and password helpers. No business logic."""
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from jose import jwt  # type: ignore[import-untyped]
from passlib.context import CryptContext  # type: ignore[import-untyped]

from app.core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return cast(str, _pwd_context.hash(password))


def verify_password(plain: str, hashed: str) -> bool:
    return cast(bool, _pwd_context.verify(plain, hashed))


def create_access_token(subject: str, ttl_seconds: int | None = None) -> str:
    expire = datetime.now(UTC) + timedelta(
        seconds=ttl_seconds if ttl_seconds is not None else settings.JWT_TTL_SECONDS
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    return cast(str, jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG))


def decode_token(token: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG]),
    )
