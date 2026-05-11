import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "../lib/cn.js";

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  function Card({ className, ...rest }, ref) {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-lg border border-border bg-surface p-6 shadow-sm",
          className,
        )}
        {...rest}
      />
    );
  },
);
