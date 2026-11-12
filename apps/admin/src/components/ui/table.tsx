"use client";
import { cn, Icon } from "@dtmai/ui";
import type { ReactNode } from "react";
import { useT } from "@/lib/i18n";
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

export function DataTable<T>({ rows, cols, rowKey, onRow, loading, error, empty, selected, rowClass, sort, onSort }: {
  rows: T[] | undefined; cols: Col<T>[]; rowKey: (r: T) => string; onRow?: (r: T) => void;
  loading?: boolean; error?: unknown; empty?: ReactNode; selected?: string | null; rowClass?: (r: T) => string | undefined;
  sort?: SortState; onSort?: (key: string) => void;
}) {
  const t = useT();
  if (error) return <ErrorBox error={error} />;
  if (loading) return <div className="grid place-items-center p-8"><Spinner /></div>;
  if (!rows || rows.length === 0) return <Empty>{empty ?? t("admin.common.nothingYet")}</Empty>;
  return (
    <div className="max-h-full max-w-full overflow-auto">
    <table className="w-full min-w-max border-collapse text-sm">
      <thead className="sticky top-0 z-10 bg-snow text-left text-xs uppercase tracking-wide text-ink-soft">
        <tr>{cols.map((c) => <th key={c.key} aria-sort={c.sortKey && sort?.key === c.sortKey ? (sort.order === "asc" ? "ascending" : "descending") : undefined} className={cn("border-b border-line px-3 py-1.5 font-extrabold", c.className)}>
          {c.sortKey && onSort ? (
            <button type="button" onClick={() => onSort(c.sortKey!)} className="inline-flex items-center gap-1 uppercase hover:text-ink">
              {c.head}{sort?.key === c.sortKey && <Icon name={sort.order === "asc" ? "arrow-up" : "arrow-down"} size={16} />}
            </button>
          ) : c.head}
        </th>)}</tr>
      </thead>
      <tbody>
        {rows.map((r, i) => {
          const k = rowKey(r);
          return (
            <tr key={k} onClick={onRow ? () => onRow(r) : undefined}
              tabIndex={onRow ? 0 : undefined}
              onKeyDown={onRow ? (e) => { if (e.target === e.currentTarget && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); onRow(r); } } : undefined}
              className={cn("border-b border-line bg-white", onRow && "cursor-pointer hover:bg-blue-soft/50 focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-blue", selected === k && "bg-blue-soft", rowClass?.(r))}>
              {cols.map((c) => <td key={c.key} className={cn("px-3 py-1.5 align-middle", c.className)}>{c.cell(r, i)}</td>)}
            </tr>
          );
        })}
      </tbody>
    </table>
    </div>
  );
}
