"use client";
import { Btn, Select } from "./controls";

export const PAGE_SIZES = [10, 25, 50, 100] as const;

/** Server-paging footer: range, page size and prev/next. Pages are 1-based. */
export function Pager({ page, size, total, onPage, onSize }: { page: number; size: number; total: number; onPage: (p: number) => void; onSize: (s: number) => void }) {
  const pages = Math.max(1, Math.ceil(total / size));
  const from = total === 0 ? 0 : (page - 1) * size + 1;
  const to = Math.min(total, page * size);
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-t border-line bg-white px-4 py-2 text-xs text-ink-soft">
      <span>{from}–{to} of {total}</span>
      <div className="flex items-center gap-2">
        <label className="flex items-center gap-1">Rows
          <Select className="w-20 py-1" value={size} onChange={(e) => onSize(Number(e.target.value))}>{PAGE_SIZES.map((s) => <option key={s} value={s}>{s}</option>)}</Select>
        </label>
        <Btn disabled={page <= 1} onClick={() => onPage(page - 1)} aria-label="Previous page">‹</Btn>
        <span className="tabular-nums">{page} / {pages}</span>
        <Btn disabled={page >= pages} onClick={() => onPage(page + 1)} aria-label="Next page">›</Btn>
      </div>
    </div>
  );
}

export type Order = "asc" | "desc";
/** Next sort state when a header is clicked: new key → desc first, same key → toggle. */
export function nextSort<K extends string>(cur: { key: K; order: Order }, key: K): { key: K; order: Order } {
  return cur.key === key ? { key, order: cur.order === "asc" ? "desc" : "asc" } : { key, order: "desc" };
}
