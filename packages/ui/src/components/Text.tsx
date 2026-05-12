import { forwardRef, type HTMLAttributes, type ElementType } from "react";
import { cn } from "../lib/cn.js";

type Size = "xs" | "sm" | "base" | "lg" | "xl" | "2xl" | "3xl";
type Tone = "default" | "muted" | "danger" | "success";
type Weight = "normal" | "medium" | "semibold" | "bold";

export interface TextProps extends HTMLAttributes<HTMLElement> {
  as?: ElementType;
  size?: Size;
  tone?: Tone;
  weight?: Weight;
}

const SIZE: Record<Size, string> = {
  xs: "text-xs",
  sm: "text-sm",
  base: "text-base",
  lg: "text-lg",
  xl: "text-xl",
  "2xl": "text-2xl",
  "3xl": "text-3xl",
};

const TONE: Record<Tone, string> = {
  default: "text-text",
  muted: "text-text-muted",
  danger: "text-danger",
  success: "text-success",
};

const WEIGHT: Record<Weight, string> = {
  normal: "font-normal",
  medium: "font-medium",
  semibold: "font-semibold",
  bold: "font-bold",
};

export const Text = forwardRef<HTMLElement, TextProps>(function Text(
  { as: Component = "p", className, size = "base", tone = "default", weight, ...rest },
  ref,
) {
  return (
    <Component
      ref={ref as never}
      className={cn(SIZE[size], TONE[tone], weight && WEIGHT[weight], className)}
      {...rest}
    />
  );
});
