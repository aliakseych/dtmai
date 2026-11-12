"use client";
import { useCallback, useEffect, useLayoutEffect, useId, useRef, useState, type KeyboardEvent as ReactKeyboardEvent, type ReactNode } from "react";
import { cn } from "../cn";

export type LanguageOption = { value: string; label: string; flag: ReactNode; /** Compact label (e.g. "UZ") shown below `sm`. */ short?: string };

/**
 * Duolingo-style language picker: an uppercase "SITE LANGUAGE: NAME ⌄" trigger
 * opening a bordered popover with a caret and a 2-column grid of flag + name.
 * Keyboard: Enter/Space/ArrowDown open, arrows move, Enter selects, Esc/outside click closes.
 */
export function LanguageSelector({
  value,
  options,
  onChange,
  label,
  placement = "bottom",
  align = "start",
  className,
  compact = false,
}: {
  value: string;
  options: LanguageOption[];
  onChange: (value: string) => void;
  /** Caption before the current language, e.g. "Site language". */
  label: string;
  placement?: "bottom" | "top";
  align?: "start" | "end";
  className?: string;
  /** Always show the short label (narrow sidebars). */
  compact?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const items = useRef<(HTMLButtonElement | null)[]>([]);
  const popover = useRef<HTMLDivElement>(null);
  const [shift, setShift] = useState(0);
  const listId = useId();
  const current = options.find((o) => o.value === value) ?? options[0];

  const close = useCallback((restoreFocus: boolean) => {
    setOpen(false);
    if (restoreFocus) trigger.current?.focus();
  }, []);

  useEffect(() => {
    if (!open) return;
    const idx = Math.max(0, options.findIndex((o) => o.value === value));
    items.current[idx]?.focus();
    const onPointer = (e: PointerEvent) => {
      if (root.current && !root.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", onPointer);
    return () => document.removeEventListener("pointerdown", onPointer);
  }, [open, options, value]);

  // Keep the popover inside the viewport regardless of where the trigger sits.
  useLayoutEffect(() => {
    if (!open) return;
    const el = popover.current;
    if (!el) return;
    const margin = 8;
    const rect = el.getBoundingClientRect();
    const base = rect.left - shift;
    const vw = document.documentElement.clientWidth;
    const next = Math.max(margin - base, Math.min(0, vw - margin - (base + rect.width)));
    if (next !== shift) setShift(next);
  }, [open, shift]);

  const move = (from: number, delta: number) => {
    const n = options.length;
    items.current[(from + delta + n) % n]?.focus();
  };

  const onListKey = (e: ReactKeyboardEvent, i: number) => {
    switch (e.key) {
      case "Escape":
        e.preventDefault();
        close(true);
        break;
      case "ArrowRight":
        e.preventDefault();
        move(i, 1);
        break;
      case "ArrowLeft":
        e.preventDefault();
        move(i, -1);
        break;
      case "ArrowDown":
        e.preventDefault();
        move(i, i + 2 < options.length ? 2 : 0);
        break;
      case "ArrowUp":
        e.preventDefault();
        move(i, i - 2 >= 0 ? -2 : 0);
        break;
      case "Home":
        e.preventDefault();
        items.current[0]?.focus();
        break;
      case "End":
        e.preventDefault();
        items.current[options.length - 1]?.focus();
        break;
      case "Tab":
        setOpen(false);
        break;
    }
  };

  return (
    <div ref={root} className={cn("relative inline-block", className)}>
      <button
        ref={trigger}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? listId : undefined}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={(e) => {
          if (e.key === "ArrowDown" && !open) {
            e.preventDefault();
            setOpen(true);
          }
        }}
        className="inline-flex min-h-11 items-center gap-2 rounded-xl px-2 text-[13px] font-extrabold uppercase tracking-wide text-ink-soft transition hover:bg-snow hover:text-ink"
      >
        <span className="shrink-0 overflow-hidden rounded-[3px] [&>svg]:block [&>svg]:h-4 [&>svg]:w-6">{current?.flag}</span>
        <span className={cn("whitespace-nowrap", !compact && "sm:hidden")}>{current?.short ?? current?.label}</span>
        <span className={cn("hidden whitespace-nowrap", !compact && "sm:inline")}>
          {label}: {current?.label}
        </span>
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          aria-hidden
          className={cn("shrink-0 transition-transform", open && "rotate-180")}
        >
          <path d="m5 9 7 7 7-7" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      {open && (
        <div
          ref={popover}
          style={shift ? { translate: `${shift}px 0` } : undefined}
          className={cn(
            "menu-in absolute z-50 w-[19rem] max-w-[calc(100vw-2rem)] rounded-2xl border-2 border-line bg-white p-2 shadow-xl",
            placement === "bottom" ? "top-full mt-3" : "bottom-full mb-3",
            align === "start" ? "left-0" : "right-0",
          )}
        >
          <span
            aria-hidden
            className={cn(
              "absolute size-3.5 rotate-45 border-line bg-white",
              placement === "bottom" ? "-top-[9px] border-l-2 border-t-2" : "-bottom-[9px] border-b-2 border-r-2",
              align === "start" ? "left-8" : "right-8",
            )}
            style={shift ? { translate: `${-shift}px 0` } : undefined}
          />
          <div id={listId} role="listbox" aria-label={label} className="relative grid grid-cols-2 gap-1">
            {options.map((o, i) => {
              const selected = o.value === value;
              return (
                <button
                  key={o.value}
                  ref={(el) => {
                    items.current[i] = el;
                  }}
                  type="button"
                  role="option"
                  aria-selected={selected}
                  onKeyDown={(e) => onListKey(e, i)}
                  onClick={() => {
                    onChange(o.value);
                    close(true);
                  }}
                  className={cn(
                    "flex items-center gap-2.5 rounded-xl border-2 min-h-11 px-3 py-2 text-left text-[15px] font-extrabold transition",
                    selected ? "border-brand bg-brand-soft text-brand" : "border-transparent text-ink hover:bg-snow",
                  )}
                >
                  <span className="shrink-0 overflow-hidden rounded-[3px] shadow-[0_0_0_1px_rgba(0,0,0,.08)] [&>svg]:block [&>svg]:h-5 [&>svg]:w-[30px]">
                    {o.flag}
                  </span>
                  <span className="truncate">{o.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
