"use client";
import { useEffect, useRef, useState } from "react";
import { cn } from "../cn";
import { ChoiceList, type ChoiceItem } from "./ChoiceList";

/** Collapsed ChoiceList: a trigger showing the current choice that opens the searchable list in a popover. */
export function ChoiceDropdown({
  items,
  pinned = [],
  value,
  onChange,
  label,
  searchPlaceholder,
  emptyText,
  className,
}: {
  items: ChoiceItem[];
  pinned?: ChoiceItem[];
  value: string | null;
  onChange: (value: string) => void;
  label: string;
  searchPlaceholder?: string;
  emptyText?: string;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const onPointer = (e: PointerEvent) => {
      if (root.current && !root.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);
  const current = [...pinned, ...items].find((i) => i.value === value);
  return (
    <div ref={root} className={cn("relative", className)}>
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={label}
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 rounded-2xl border-2 border-line bg-snow px-4 py-3 text-left font-bold text-ink focus:border-brand focus:bg-white"
      >
        <span className="min-w-0 flex-1 truncate">{current?.label ?? label}</span>
        <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden className={cn("shrink-0 transition-transform", open && "rotate-180")}>
          <path d="m5 9 7 7 7-7" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      {open && (
        <div className="absolute right-0 z-40 mt-2 w-full min-w-64 max-w-[calc(100vw-2rem)] rounded-2xl border-2 border-line bg-white p-2 shadow-xl">
          <ChoiceList
            label={label}
            items={items}
            pinned={pinned}
            value={value}
            onChange={(v) => {
              onChange(v);
              setOpen(false);
            }}
            searchPlaceholder={searchPlaceholder}
            emptyText={emptyText}
          />
        </div>
      )}
    </div>
  );
}
