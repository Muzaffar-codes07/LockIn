import { z } from "zod";

export const EVENT_VERSION = 1 as const;

export const EventSource = z.enum(["web", "mcp", "api", "agent"]);
export type EventSource = z.infer<typeof EventSource>;

export const eventEnvelope = <T extends z.ZodTypeAny>(payload: T, eventType: string) =>
  z.object({
    event_id: z.string().uuid(),
    event_type: z.literal(eventType),
    event_version: z.literal(EVENT_VERSION),
    user_id: z.string().uuid(),
    tenant_id: z.string().uuid().nullable(),
    occurred_at: z.string().datetime({ offset: true }),
    client_idempotency_key: z.string().min(1).max(128).nullable(),
    source: EventSource,
    payload,
  });

export type EventEnvelope<T> = {
  event_id: string;
  event_type: string;
  event_version: typeof EVENT_VERSION;
  user_id: string;
  tenant_id: string | null;
  occurred_at: string;
  client_idempotency_key: string | null;
  source: EventSource;
  payload: T;
};
