/**
 * LockIn Event Schema — v1
 *
 * This file defines the immutable event contract. Every user action emits one
 * of these events to Redis Streams. The schema is versioned; breaking changes
 * require a new version and migration path.
 *
 * Rules:
 *   - event_version is MANDATORY on every event
 *   - New fields MUST be optional (forward compatibility)
 *   - Removing fields requires incrementing event_version
 *   - Every event has: event_id (uuid), event_type, event_version, user_id,
 *     emitted_at (ISO 8601), idempotency_key, payload
 */

export type EventVersion = 1;

export interface EventEnvelope<TPayload> {
  event_id: string;            // uuid v7 preferred (time-ordered)
  event_type: string;          // dotted namespace: "task.created"
  event_version: EventVersion;
  user_id: string;
  emitted_at: string;          // ISO 8601 UTC
  idempotency_key: string;     // client-generated; server dedups
  payload: TPayload;
}

// ---------------------------------------------------------------------------
// TASK EVENTS
// ---------------------------------------------------------------------------

export interface TaskCreatedPayload {
  task_id: string;
  title: string;
  source: "keyboard" | "click" | "voice" | "mcp";
  // Optional fields for future slices — safe to add because they're optional:
  due_date?: string;           // ISO 8601
  priority?: "low" | "medium" | "high";
  estimated_minutes?: number;
}

export type TaskCreatedEvent = EventEnvelope<TaskCreatedPayload> & {
  event_type: "task.created";
};

export interface TaskDeletedPayload {
  task_id: string;
  reason?: "user" | "agent" | "completed";
}

export type TaskDeletedEvent = EventEnvelope<TaskDeletedPayload> & {
  event_type: "task.deleted";
};

// ---------------------------------------------------------------------------
// MOOD / ENERGY EVENTS — scaffolded for later slices, do NOT implement yet
// ---------------------------------------------------------------------------

export interface MoodLoggedPayload {
  mood: 1 | 2 | 3 | 4 | 5;
  energy: 1 | 2 | 3 | 4 | 5;
  context?: "morning" | "post_lunch" | "mid_afternoon" | "evening";
}

export type MoodLoggedEvent = EventEnvelope<MoodLoggedPayload> & {
  event_type: "mood.logged";
};

// ---------------------------------------------------------------------------
// UNION TYPE — add new events here as slices land
// ---------------------------------------------------------------------------

export type LockInEvent =
  | TaskCreatedEvent
  | TaskDeletedEvent
  | MoodLoggedEvent;

// ---------------------------------------------------------------------------
// REDIS STREAM NAMES — single source of truth
// ---------------------------------------------------------------------------

export const STREAM_NAMES = {
  TASKS: "events:tasks",
  MOOD: "events:mood",
  SCHEDULE: "events:schedule",
  AGENT: "events:agent",
} as const;
