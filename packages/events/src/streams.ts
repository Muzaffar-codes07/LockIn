export const STREAM_NAMES = {
  TASKS: "events:tasks",
  SIGNALS: "events:signals",
  SCHEDULE: "events:schedule",
  AGENT: "events:agent",
} as const;

export type StreamName = (typeof STREAM_NAMES)[keyof typeof STREAM_NAMES];

export const EVENT_TYPE_TO_STREAM: Record<string, StreamName> = {
  "task.created": STREAM_NAMES.TASKS,
  "task.scheduled": STREAM_NAMES.SCHEDULE,
  "task.accepted": STREAM_NAMES.SCHEDULE,
  "task.rejected": STREAM_NAMES.SCHEDULE,
  "task.modified": STREAM_NAMES.TASKS,
  "task.completed": STREAM_NAMES.TASKS,
  "mood.logged": STREAM_NAMES.SIGNALS,
  "energy.logged": STREAM_NAMES.SIGNALS,
  "schedule.explained": STREAM_NAMES.AGENT,
};
