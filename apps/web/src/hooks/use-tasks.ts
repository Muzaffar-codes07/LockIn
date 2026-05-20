"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { TaskCreateRequest, TaskResponse } from "@lockin/shared-types";

const TASKS_KEY = ["tasks"] as const;

async function fetchTasks(): Promise<TaskResponse[]> {
  const res = await fetch("/api/tasks", { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Failed to load tasks");
  }
  return res.json();
}

async function createTask(input: TaskCreateRequest): Promise<TaskResponse> {
  const res = await fetch("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    throw new Error("Failed to create task");
  }
  return res.json();
}

export function useTasks() {
  return useQuery({ queryKey: TASKS_KEY, queryFn: fetchTasks });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createTask,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TASKS_KEY }),
  });
}
