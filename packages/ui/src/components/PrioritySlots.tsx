import type { ReactNode } from "react";
import { Icon } from "./icons";

export interface PriorityItem {
  id: string;
  label: ReactNode;
}

export interface PrioritySlotsProps {
  items: readonly PriorityItem[];
  /** Number of slots shown (empty ones render as placeholders). */
  max?: number;
  emptyText: string;
  /** Accessible labels for the row controls. */
  labels: { up: string; down: string; remove: string; slot: (n: number) => string };
  onMove: (from: number, to: number) => void;
  onRemove: (id: string) => void;
  disabled?: boolean;
  className?: string;
}

const iconBtn =
  "grid size-10 shrink-0 place-items-center rounded-xl border-2 border-line bg-white text-ink-soft transition-colors hover:border-brand hover:text-brand focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue disabled:cursor-not-allowed disabled:opacity-40";

/** Ordered 1-2-3 priority list: numbered slots with move up / down / remove controls. */
export function PrioritySlots({ items, max = 3, emptyText, labels, onMove, onRemove, disabled, className = "" }: PrioritySlotsProps) {
  return (
    <ol className={`flex flex-col gap-2 ${className}`}>
      {Array.from({ length: max }, (_, i) => {
        const item = items[i];
        return (
          <li
            key={item?.id ?? `empty-${i}`}
            className={`flex flex-wrap items-center gap-x-3 gap-y-1 rounded-2xl border-2 px-3 py-2 ${
              item ? "border-brand bg-brand-soft" : "border-dashed border-line bg-snow"
            }`}
          >
            <span
              aria-label={labels.slot(i + 1)}
              className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-base font-extrabold ${
                item ? "bg-brand text-white" : "bg-white text-ink-soft"
              }`}
            >
              {i + 1}
            </span>
            {item ? (
              <>
                <div className="min-w-[10rem] flex-1 break-words font-bold text-ink">{item.label}</div>
                <button type="button" className={iconBtn} disabled={disabled || i === 0} onClick={() => onMove(i, i - 1)} aria-label={labels.up}>
                  <Icon name="arrow-up" size={20} />
                </button>
                <button
                  type="button"
                  className={iconBtn}
                  disabled={disabled || i === items.length - 1}
                  onClick={() => onMove(i, i + 1)}
                  aria-label={labels.down}
                >
                  <Icon name="arrow-down" size={20} />
                </button>
                <button type="button" className={iconBtn} disabled={disabled} onClick={() => onRemove(item.id)} aria-label={labels.remove}>
                  <Icon name="close" size={20} />
                </button>
              </>
            ) : (
              <span className="text-sm font-bold text-ink-soft">{emptyText}</span>
            )}
          </li>
        );
      })}
    </ol>
  );
}
