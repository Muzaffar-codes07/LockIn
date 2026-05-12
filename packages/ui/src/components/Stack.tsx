import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "../lib/cn.js";

export interface StackProps extends HTMLAttributes<HTMLDivElement> {
  direction?: "row" | "col";
  gap?: 1 | 2 | 3 | 4 | 6 | 8 | 12;
  align?: "start" | "center" | "end" | "stretch";
  justify?: "start" | "center" | "end" | "between";
}

const GAP: Record<NonNullable<StackProps["gap"]>, string> = {
  1: "gap-1",
  2: "gap-2",
  3: "gap-3",
  4: "gap-4",
  6: "gap-6",
  8: "gap-8",
  12: "gap-12",
};

const ALIGN: Record<NonNullable<StackProps["align"]>, string> = {
  start: "items-start",
  center: "items-center",
  end: "items-end",
  stretch: "items-stretch",
};

const JUSTIFY: Record<NonNullable<StackProps["justify"]>, string> = {
  start: "justify-start",
  center: "justify-center",
  end: "justify-end",
  between: "justify-between",
};

export const Stack = forwardRef<HTMLDivElement, StackProps>(function Stack(
  { className, direction = "col", gap = 4, align, justify, ...rest },
  ref,
) {
  return (
    <div
      ref={ref}
      className={cn(
        "flex",
        direction === "row" ? "flex-row" : "flex-col",
        GAP[gap],
        align && ALIGN[align],
        justify && JUSTIFY[justify],
        className,
      )}
      {...rest}
    />
  );
});
