"use client";
import type { KeyboardEvent } from "react";
import { cn } from "../cn";

export type TabItem<T extends string> = { id: T; label: string };

export function Tabs<T extends string>({
  items,
  value,
  onChange,
  className,
}: {
  items: TabItem<T>[];
  value: T;
  onChange: (id: T) => void;
  className?: string;
}) {
  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const i = items.findIndex((x) => x.id === value);
    let n = -1;
    if (e.key === "ArrowRight") n = (i + 1) % items.length;
    else if (e.key === "ArrowLeft") n = (i - 1 + items.length) % items.length;
    else if (e.key === "Home") n = 0;
    else if (e.key === "End") n = items.length - 1;
    if (n < 0) return;
    e.preventDefault();
    onChange(items[n].id);
    (e.currentTarget.querySelectorAll<HTMLElement>('[role="tab"]')[n])?.focus();
  };
  return (
    <div role="tablist" onKeyDown={onKeyDown} className={cn("flex gap-2 overflow-x-auto", className)}>
      {items.map((it) => {
        const on = it.id === value;
        return (
          <button
            key={it.id}
            role="tab"
            aria-selected={on}
            tabIndex={on ? 0 : -1}
            type="button"
            onClick={() => onChange(it.id)}
            className={cn(
              "min-h-11 shrink-0 rounded-xl border-2 px-4 py-2 text-sm font-extrabold uppercase tracking-wide transition",
              on ? "border-brand bg-brand-soft text-brand" : "border-line bg-white text-ink-soft hover:bg-snow",
            )}
          >
            {it.label}
          </button>
        );
      })}
    </div>
  );
}
