import { forwardRef, type SVGAttributes, type ReactNode } from "react";
import { cn } from "../lib/cn.js";

export interface IconProps extends Omit<SVGAttributes<SVGSVGElement>, "children"> {
  label?: string;
  size?: 16 | 20 | 24 | 32;
  children: ReactNode;
}

export const Icon = forwardRef<SVGSVGElement, IconProps>(function Icon(
  { label, size = 20, className, children, ...rest },
  ref,
) {
  const decorative = !label;
  return (
    <svg
      ref={ref}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={decorative || undefined}
      aria-label={label}
      role={decorative ? undefined : "img"}
      className={cn("inline-block shrink-0", className)}
      {...rest}
    >
      {children}
    </svg>
  );
});
