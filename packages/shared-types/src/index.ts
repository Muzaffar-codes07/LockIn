// Shared API request/response types. Must stay in sync with
// apps/api/app/schemas/task.py.

export type TaskSource = "keyboard" | "click" | "voice" | "mcp";

export interface TaskCreateRequest {
  /** 1–500 characters. Enforced server-side by the API schema. */
  title: string;
  source?: TaskSource;
}

export interface TaskResponse {
  id: string;
  title: string;
  // Intentionally `string`, not `TaskSource`: mirrors the API's forward-compatible
  // `str` typing so new source values don't break deserialization.
  source: string;
  created_at: string;
}
