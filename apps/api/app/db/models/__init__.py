"""SQLAlchemy ORM models.

Importing this package side-effects: every model module here is loaded so
``Base.metadata`` sees the tables. Alembic's ``env.py`` imports this package
for the same reason — see the note in ``alembic/env.py``.
"""

from app.db.models.behavior_event import BehaviorEvent  # noqa: F401
from app.db.models.calendar_event import CalendarEvent  # noqa: F401
from app.db.models.credential import WebauthnCredential  # noqa: F401
from app.db.models.energy_log import EnergyLog  # noqa: F401
from app.db.models.explanation import Explanation  # noqa: F401
from app.db.models.idempotency_key import IdempotencyKey  # noqa: F401
from app.db.models.mood_log import MoodLog  # noqa: F401
from app.db.models.oauth_token import OAuthToken  # noqa: F401
from app.db.models.schedule_slot import ScheduleSlot  # noqa: F401
from app.db.models.task import Task  # noqa: F401

__all__ = [
    "BehaviorEvent",
    "CalendarEvent",
    "EnergyLog",
    "Explanation",
    "IdempotencyKey",
    "MoodLog",
    "OAuthToken",
    "ScheduleSlot",
    "Task",
    "WebauthnCredential",
]
