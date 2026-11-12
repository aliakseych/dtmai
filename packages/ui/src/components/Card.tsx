import type { HTMLAttributes } from "react";
import { cn } from "../cn";

const PAD = { none: "", sm: "p-4", md: "p-5" } as const;

/** Flat surface. `cn` does not merge classes, so padding is a prop: never pass `p-*` in `className`. */
export function cardClass(pad: keyof typeof PAD = "md", interactive = false, extra?: string) {
  return cn("rounded-card border-2 border-line bg-white", PAD[pad], interactive && "border-b-4 transition-colors hover:bg-snow", extra);
}

export function Card({
  className,
  pad = "md",
  interactive = false,
  ...rest
}: HTMLAttributes<HTMLDivElement> & { pad?: keyof typeof PAD; interactive?: boolean }) {
  return <div className={cardClass(pad, interactive, className)} {...rest} />;
}
