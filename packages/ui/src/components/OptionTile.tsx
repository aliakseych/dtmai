"use client";
import { useEffect, useRef, type KeyboardEvent, type ReactNode } from "react";
import { cn } from "../cn";
import { CheckIcon, CrossIcon } from "./icons";

export type OptionState = "idle" | "selected" | "correct" | "incorrect";

const STATES: Record<OptionState, string> = {
  idle: "border-line bg-white hover:bg-snow",
  selected: "border-blue bg-blue-soft text-[#0d5f8a]",
  correct: "border-green-deep bg-green-soft text-[#2f6200]",
  incorrect: "border-red-deep bg-red-soft text-[#a11c1c]",
};

/** Radiogroup wrapper: roving tabindex + arrow keys (arrows move focus and select, like native radios). */
export function OptionGroup({
  label,
  multi,
  className,
  children,
}: {
  label: string;
  multi?: boolean;
  className?: string;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const items = Array.from(ref.current?.querySelectorAll<HTMLElement>("[data-option]") ?? []);
    const checked = items.findIndex((el) => el.getAttribute("aria-checked") === "true");
    const stop = checked >= 0 ? checked : items.findIndex((el) => !(el as HTMLButtonElement).disabled);
    items.forEach((el, i) => el.setAttribute("tabindex", multi || i === stop ? "0" : "-1"));
  });
  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (multi) return;
    const fwd = e.key === "ArrowDown" || e.key === "ArrowRight";
    const back = e.key === "ArrowUp" || e.key === "ArrowLeft";
    if (!fwd && !back) return;
    const items = Array.from(ref.current?.querySelectorAll<HTMLButtonElement>("[data-option]:not(:disabled)") ?? []);
    if (!items.length) return;
    e.preventDefault();
    const cur = items.indexOf(document.activeElement as HTMLButtonElement);
    const next = items[(cur + (fwd ? 1 : -1) + items.length) % items.length];
    next.focus();
    next.click();
  };
  return (
    <div ref={ref} role={multi ? "group" : "radiogroup"} aria-label={label} onKeyDown={onKeyDown} className={className}>
      {children}
    </div>
  );
}

export function OptionTile({
  index,
  state = "idle",
  disabled,
  multi,
  onSelect,
  children,
}: {
  /** 0-based; shown as A–D and bound to keys 1–9 */
  index: number;
  state?: OptionState;
  disabled?: boolean;
  multi?: boolean;
  onSelect: () => void;
  children: ReactNode;
}) {
  useEffect(() => {
    if (disabled || index > 8) return;
    const handler = (e: globalThis.KeyboardEvent) => {
      const el = e.target as HTMLElement | null;
      if (el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable)) return;
      if (e.key === String(index + 1)) onSelect();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [index, disabled, onSelect]);

  const on = state === "selected" || state === "correct" || state === "incorrect";
  return (
    <button
      type="button"
      data-option
      role={multi ? "checkbox" : "radio"}
      aria-checked={on}
      aria-invalid={state === "incorrect" || undefined}
      disabled={disabled}
      onClick={onSelect}
      className={cn(
        "flex w-full items-center gap-3 rounded-2xl border-2 border-b-4 px-4 py-3 text-left text-[17px] font-bold transition active:translate-y-[2px] active:border-b-2 disabled:cursor-default disabled:active:translate-y-0 disabled:active:border-b-4",
        STATES[state],
      )}
    >
      <span
        className={cn(
          "grid h-8 w-8 shrink-0 place-items-center rounded-lg border-2 border-current text-sm font-extrabold",
          state === "selected" && "bg-current",
        )}
      >
        <span className={state === "selected" ? "text-white" : undefined}>{String.fromCharCode(65 + index)}</span>
      </span>
      <span className="flex-1">{children}</span>
      {state === "correct" && <CheckIcon aria-hidden width={24} height={24} />}
      {state === "incorrect" && <CrossIcon aria-hidden width={24} height={24} />}
      <kbd className="hidden text-xs opacity-60 sm:inline">{index + 1}</kbd>
    </button>
  );
}
