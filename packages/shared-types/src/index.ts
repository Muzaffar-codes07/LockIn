// Shared API request/response types. Must stay in sync with
// apps/api/app/schemas/task.py.

export type TaskSource = "keyboard" | "click" | "voice" | "mcp";

export interface TaskCreateRequest {
  title: string;
  source?: TaskSource;
}

export interface TaskResponse {
  id: string;
  title: string;
  source: string;
  created_at: string;
}
