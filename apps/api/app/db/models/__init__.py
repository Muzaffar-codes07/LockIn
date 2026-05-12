"""SQLAlchemy ORM models.

Importing this package side-effects: every model module here is loaded so
``Base.metadata`` sees the tables. Alembic's ``env.py`` imports this package
for the same reason — see the note in ``alembic/env.py``.
"""

from app.db.models.credential import WebauthnCredential  # noqa: F401

__all__ = ["WebauthnCredential"]
