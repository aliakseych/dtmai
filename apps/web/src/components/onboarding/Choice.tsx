"use client";
import type { ReactNode } from "react";
import { cn } from "@dtmai/ui";

/** Duolingo-style selectable answer card (radio or checkbox semantics via `multi`). */
export function Choice({ on, onClick, multi, children }: { on: boolean; onClick: () => void; multi?: boolean; children: ReactNode }) {
  return (
    <button
      type="button"
      role={multi ? "checkbox" : "radio"}
      aria-checked={on}
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-3 rounded-2xl border-2 border-b-4 px-4 py-3 text-left font-extrabold transition-colors",
        on ? "border-blue bg-blue-soft text-blue-deep" : "border-line bg-white hover:bg-snow",
      )}
    >
      {children}
    </button>
  );
}
