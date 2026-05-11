from typing import Final

STREAM_TASKS: Final[str] = "events:tasks"
STREAM_SIGNALS: Final[str] = "events:signals"
STREAM_SCHEDULE: Final[str] = "events:schedule"
STREAM_AGENT: Final[str] = "events:agent"

EVENT_TYPE_TO_STREAM: Final[dict[str, str]] = {
    "task.created": STREAM_TASKS,
    "task.scheduled": STREAM_SCHEDULE,
    "task.accepted": STREAM_SCHEDULE,
    "task.rejected": STREAM_SCHEDULE,
    "task.modified": STREAM_TASKS,
    "task.completed": STREAM_TASKS,
    "mood.logged": STREAM_SIGNALS,
    "energy.logged": STREAM_SIGNALS,
    "schedule.explained": STREAM_AGENT,
}
