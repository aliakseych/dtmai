"use client";
import { cn } from "@dtmai/ui";
import type { ReactNode } from "react";
import { Empty, ErrorBox, Spinner } from "./controls";

export interface Col<T> {
  key: string;
  head: ReactNode;
  cell: (row: T, i: number) => ReactNode;
  className?: string;
}

export function DataTable<T>({ rows, cols, rowKey, onRow, loading, error, empty = "Nothing here yet.", selected, rowClass }: {
  rows: T[] | undefined; cols: Col<T>[]; rowKey: (r: T) => string; onRow?: (r: T) => void;
  loading?: boolean; error?: unknown; empty?: ReactNode; selected?: string | null; rowClass?: (r: T) => string | undefined;
}) {
  if (error) return <ErrorBox error={error} />;
  if (loading) return <div className="grid place-items-center p-8"><Spinner /></div>;
  if (!rows || rows.length === 0) return <Empty>{empty}</Empty>;
  return (
    <table className="w-full border-collapse text-[13px]">
      <thead className="sticky top-0 z-10 bg-snow text-left text-[11px] uppercase tracking-wide text-ink-soft">
        <tr>{cols.map((c) => <th key={c.key} className={cn("border-b border-line px-3 py-1.5 font-extrabold", c.className)}>{c.head}</th>)}</tr>
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
  );
}
