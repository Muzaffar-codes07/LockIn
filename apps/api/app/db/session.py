"""Async engine + session factory.

The FastAPI dependency lives in `app/api/v1/deps.py` (`_db_session`); this
module exposes only the raw factory used by `deps.py`, alembic, and tests.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
