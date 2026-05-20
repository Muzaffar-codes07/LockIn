"use client";

import { useEffect, useRef, useState } from "react";
import { Button, Input, Stack, Text } from "@lockin/ui";

export interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (title: string) => void;
}

export function CommandPalette({ open, onOpenChange, onSubmit }: CommandPaletteProps) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        onOpenChange(!open);
      }
      if (e.key === "Escape") {
        onOpenChange(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onOpenChange]);

  useEffect(() => {
    if (open) {
      inputRef.current?.focus();
    } else {
      setValue("");
    }
  }, [open]);

  if (!open) {
    return null;
  }

  function submit() {
    const title = value.trim();
    if (!title) {
      return;
    }
    onSubmit(title);
    setValue("");
    onOpenChange(false);
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Add a task"
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 pt-32"
      onClick={() => onOpenChange(false)}
    >
      <div
        className="w-full max-w-lg rounded-lg bg-surface p-4 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <Stack gap={3}>
          <Text size="sm" tone="muted">
            Add a task
          </Text>
          <Input
            ref={inputRef}
            value={value}
            placeholder="What needs doing?"
            aria-label="Task title"
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                submit();
              }
            }}
          />
          <Button variant="primary" onClick={submit}>
            Add task
          </Button>
        </Stack>
      </div>
    </div>
  );
}
