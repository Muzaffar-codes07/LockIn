"use client";

import { useState } from "react";
import { Button, Card, Stack, Text } from "@lockin/ui";
import { CommandPalette } from "@/components/command-palette";
import { useCreateTask, useDeleteTask, useTasks } from "@/hooks/use-tasks";

export function DashboardClient() {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const { data: tasks = [], isPending } = useTasks();
  const createTask = useCreateTask();
  const deleteTask = useDeleteTask();

  return (
    <main className="mx-auto w-full max-w-2xl p-6">
      <Stack gap={6}>
        <Text as="h1" size="3xl" weight="bold">
          Today
        </Text>

        <Button variant="secondary" onClick={() => setPaletteOpen(true)}>
          Add a task — ⌘K
        </Button>

        {createTask.isError ? (
          <Text tone="danger" role="alert">
            Couldn&apos;t add task: {(createTask.error as Error).message}
          </Text>
        ) : null}

        {deleteTask.isError ? (
          <Text tone="danger" role="alert">
            Couldn&apos;t delete task: {(deleteTask.error as Error).message}
          </Text>
        ) : null}

        {isPending ? (
          <Text tone="muted">Loading…</Text>
        ) : tasks.length === 0 ? (
          <Card>
            <Stack gap={2} align="center">
              <Text weight="bold">No tasks yet</Text>
              <Text tone="muted">Press ⌘K to add your first task.</Text>
            </Stack>
          </Card>
        ) : (
          <Stack gap={2}>
            {tasks.map((task) => (
              <Card key={task.id}>
                <div className="flex items-center justify-between gap-3">
                  <Text>{task.title}</Text>
                  <Button
                    variant="ghost"
                    size="sm"
                    aria-label={`Delete ${task.title}`}
                    onClick={() => deleteTask.mutate(task.id)}
                  >
                    Delete
                  </Button>
                </div>
              </Card>
            ))}
          </Stack>
        )}
      </Stack>

      <CommandPalette
        open={paletteOpen}
        onOpenChange={setPaletteOpen}
        onSubmit={(title) => createTask.mutate({ title, source: "keyboard" })}
      />
    </main>
  );
}
