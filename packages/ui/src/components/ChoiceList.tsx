"use client";
import { useMemo, useState, type ReactNode } from "react";
import { cn } from "../cn";

export interface ChoiceItem {
  value: string;
  label: string;
  /** Secondary text shown under/right of the label. */
  hint?: string;
  leading?: ReactNode;
  /** Extra strings matched by the search box. */
  keywords?: string[];
}

const tile = (on: boolean) =>
  cn(
    "flex w-full items-center gap-3 rounded-2xl border-2 border-b-4 px-4 py-3 text-left font-extrabold transition-colors",
    on ? "border-blue bg-blue-soft text-blue-deep" : "border-line bg-white hover:bg-snow",
  );

/**
 * Duolingo-style single-choice list with optional search.
 * `pinned` items are always shown above the filtered list (e.g. an "Any" choice).
 */
export function ChoiceList({
  items,
  pinned = [],
  value,
  onChange,
  label,
  searchPlaceholder,
  emptyText,
  columns = false,
  className,
}: {
  items: ChoiceItem[];
  pinned?: ChoiceItem[];
  value: string | null;
  onChange: (value: string) => void;
  label: string;
  /** Renders a search box when set. */
  searchPlaceholder?: string;
  emptyText?: string;
  /** Two columns from `sm` up. */
  columns?: boolean;
  className?: string;
}) {
  const [q, setQ] = useState("");
  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return items;
    return items.filter((i) => [i.label, i.hint ?? "", ...(i.keywords ?? [])].some((s) => s.toLowerCase().includes(needle)));
  }, [items, q]);
  const row = (i: ChoiceItem) => (
    <button key={i.value} type="button" role="radio" aria-checked={value === i.value} onClick={() => onChange(i.value)} className={tile(value === i.value)}>
      {i.leading}
      <span className="min-w-0 flex-1 break-words">{i.label}</span>
      {i.hint && <span className="shrink-0 text-sm font-bold text-ink-soft">{i.hint}</span>}
    </button>
  );
  return (
    <div className={cn("flex flex-col gap-3", className)}>
      {searchPlaceholder && (
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={searchPlaceholder}
          aria-label={searchPlaceholder}
          className="w-full rounded-2xl border-2 border-line bg-snow px-4 py-3 text-ink focus:border-blue focus:bg-white"
        />
      )}
      <div role="radiogroup" aria-label={label} className="flex flex-col gap-2">
        {pinned.map(row)}
        <div className={cn("grid max-h-[50vh] gap-2 overflow-y-auto pr-1", columns && "sm:grid-cols-2")}>{shown.map(row)}</div>
        {shown.length === 0 && emptyText && <p className="py-4 text-center text-ink-soft">{emptyText}</p>}
      </div>
    </div>
  );
}
