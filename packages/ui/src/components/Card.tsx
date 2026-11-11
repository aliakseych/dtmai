import type { HTMLAttributes } from "react";
import { cn } from "../cn";

export function Card({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-card border-2 border-line bg-white p-5", className)} {...rest} />;
}
