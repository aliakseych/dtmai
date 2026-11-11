"use client";
import { cn } from "@dtmai/ui";
import type { ReactNode } from "react";
import { Empty, ErrorBox, Spinner } from "./controls";

export interface Col<T> {
  key: string;
  head: ReactNode;
  cell: (row: T, i: number) => ReactNode;
  className?: string;
  /** Server sort key; makes the header clickable when the table has `sort` + `onSort`. */
  sortKey?: string;
}

export interface SortState { key: string; order: "asc" | "desc" }

export function DataTable<T>({ rows, cols, rowKey, onRow, loading, error, empty = "Nothing here yet.", selected, rowClass, sort, onSort }: {
  rows: T[] | undefined; cols: Col<T>[]; rowKey: (r: T) => string; onRow?: (r: T) => void;
  loading?: boolean; error?: unknown; empty?: ReactNode; selected?: string | null; rowClass?: (r: T) => string | undefined;
  sort?: SortState; onSort?: (key: string) => void;
}) {
  if (error) return <ErrorBox error={error} />;
  if (loading) return <div className="grid place-items-center p-8"><Spinner /></div>;
  if (!rows || rows.length === 0) return <Empty>{empty}</Empty>;
  return (
    <div className="max-h-full overflow-auto">
    <table className="w-full border-collapse text-[13px]">
      <thead className="sticky top-0 z-10 bg-snow text-left text-[11px] uppercase tracking-wide text-ink-soft">
        <tr>{cols.map((c) => <th key={c.key} aria-sort={c.sortKey && sort?.key === c.sortKey ? (sort.order === "asc" ? "ascending" : "descending") : undefined} className={cn("border-b border-line px-3 py-1.5 font-extrabold", c.className)}>
          {c.sortKey && onSort ? (
            <button type="button" onClick={() => onSort(c.sortKey!)} className="inline-flex items-center gap-1 uppercase hover:text-ink">
              {c.head}<span aria-hidden>{sort?.key === c.sortKey ? (sort.order === "asc" ? "▲" : "▼") : "↕"}</span>
            </button>
          ) : c.head}
        </th>)}</tr>
      </thead>
      <tbody>
        {rows.map((r, i) => {
          const k = rowKey(r);
          return (
            <tr key={k} onClick={onRow ? () => onRow(r) : undefined} className={cn("border-b border-line bg-white", onRow && "cursor-pointer hover:bg-blue-soft/50", selected === k && "bg-blue-soft", rowClass?.(r))}>
              {cols.map((c) => <td key={c.key} className={cn("px-3 py-1.5 align-middle", c.className)}>{c.cell(r, i)}</td>)}
            </tr>
          );
        })}
      </tbody>
    </table>
    </div>
  );
}
