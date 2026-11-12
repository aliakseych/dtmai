import type { HTMLAttributes } from "react";
import { cn } from "../cn";

export type BadgeTone = "neutral" | "brand" | "accent" | "danger" | "outline";

const TONE: Record<BadgeTone, string> = {
  neutral: "border-transparent bg-snow text-ink-soft",
  brand: "border-transparent bg-brand-soft text-brand",
  accent: "border-transparent bg-accent text-ink",
  danger: "border-transparent bg-red-soft text-red-ink",
  outline: "border-line bg-white text-ink-soft",
};

/** Small status pill. Put a 16px `Icon` before the text when needed. */
export function Badge({ tone = "neutral", className, ...rest }: HTMLAttributes<HTMLSpanElement> & { tone?: BadgeTone }) {
  return (
    <span
      className={cn("inline-flex shrink-0 items-center gap-1 rounded-full border-2 px-2.5 py-0.5 text-xs font-extrabold", TONE[tone], className)}
      {...rest}
    />
  );
}
