import { z } from "zod";
import { eventEnvelope } from "./envelope.js";

// ---------- Task events ----------

export const TaskCreatedPayload = z.object({
  task_id: z.string().uuid(),
  title: z.string().min(1).max(500),
  source: z.enum(["keyboard", "click", "voice", "mcp"]),
  due_date: z.string().datetime({ offset: true }).optional(),
  priority: z.enum(["low", "medium", "high"]).optional(),
  estimated_minutes: z.number().int().positive().optional(),
});
export const TaskCreatedEvent = eventEnvelope(TaskCreatedPayload, "task.created");

export const TaskScheduledPayload = z.object({
  task_id: z.string().uuid(),
  scheduled_start: z.string().datetime({ offset: true }),
  scheduled_end: z.string().datetime({ offset: true }),
  explanation_id: z.string().uuid(),
});
export const TaskScheduledEvent = eventEnvelope(TaskScheduledPayload, "task.scheduled");

export const TaskAcceptedPayload = z.object({
  task_id: z.string().uuid(),
  schedule_id: z.string().uuid(),
});
export const TaskAcceptedEvent = eventEnvelope(TaskAcceptedPayload, "task.accepted");

export const TaskRejectedPayload = z.object({
  task_id: z.string().uuid(),
  schedule_id: z.string().uuid(),
  reason: z.enum(["wrong_time", "wrong_duration", "wrong_priority", "other"]).optional(),
  free_text: z.string().max(2000).optional(),
});
export const TaskRejectedEvent = eventEnvelope(TaskRejectedPayload, "task.rejected");

export const TaskModifiedPayload = z.object({
  task_id: z.string().uuid(),
  changes: z.record(z.string(), z.unknown()),
});
export const TaskModifiedEvent = eventEnvelope(TaskModifiedPayload, "task.modified");

export const TaskCompletedPayload = z.object({
  task_id: z.string().uuid(),
  completed_at: z.string().datetime({ offset: true }),
  actual_minutes: z.number().int().nonnegative().optional(),
});
export const TaskCompletedEvent = eventEnvelope(TaskCompletedPayload, "task.completed");

// ---------- Signal events (mood + energy) ----------

export const MoodLoggedPayload = z.object({
  mood: z.union([z.literal(1), z.literal(2), z.literal(3), z.literal(4), z.literal(5)]),
  context: z.enum(["morning", "post_lunch", "mid_afternoon", "evening"]).optional(),
});
export const MoodLoggedEvent = eventEnvelope(MoodLoggedPayload, "mood.logged");

export const EnergyLoggedPayload = z.object({
  energy: z.union([z.literal(1), z.literal(2), z.literal(3), z.literal(4), z.literal(5)]),
  context: z.enum(["morning", "post_lunch", "mid_afternoon", "evening"]).optional(),
});
export const EnergyLoggedEvent = eventEnvelope(EnergyLoggedPayload, "energy.logged");

// ---------- Agent events ----------

export const ScheduleExplainedPayload = z.object({
  explanation_id: z.string().uuid(),
  task_id: z.string().uuid(),
  factors: z.array(
    z.object({
      name: z.string(),
      weight: z.number(),
      value: z.union([z.string(), z.number(), z.boolean()]),
    }),
  ),
  model_version: z.string(),
  rendered_text: z.string().max(4000),
});
export const ScheduleExplainedEvent = eventEnvelope(
  ScheduleExplainedPayload,
  "schedule.explained",
);

// ---------- Discriminated union ----------

export const LockInEvent = z.discriminatedUnion("event_type", [
  TaskCreatedEvent,
  TaskScheduledEvent,
  TaskAcceptedEvent,
  TaskRejectedEvent,
  TaskModifiedEvent,
  TaskCompletedEvent,
  MoodLoggedEvent,
  EnergyLoggedEvent,
  ScheduleExplainedEvent,
]);
export type LockInEvent = z.infer<typeof LockInEvent>;

export const EVENT_SCHEMAS = {
  "task.created": TaskCreatedEvent,
  "task.scheduled": TaskScheduledEvent,
  "task.accepted": TaskAcceptedEvent,
  "task.rejected": TaskRejectedEvent,
  "task.modified": TaskModifiedEvent,
  "task.completed": TaskCompletedEvent,
  "mood.logged": MoodLoggedEvent,
  "energy.logged": EnergyLoggedEvent,
  "schedule.explained": ScheduleExplainedEvent,
} as const;
