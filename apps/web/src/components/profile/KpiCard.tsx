import type { ReactNode } from "react";
import { Card } from "@dtmai/ui";

/** Compact KPI tile: icon + big value + label. */
export function KpiCard({ icon, value, label, className }: { icon: ReactNode; value: ReactNode; label: string; className?: string }) {
  return (
    <Card pad="sm" className={`flex min-w-0 items-center gap-3 ${className ?? ""}`}>
      <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-brand-soft text-brand">{icon}</div>
      <div className="min-w-0">
        <div className="break-words text-2xl font-extrabold leading-tight text-ink">{value}</div>
        <div className="break-words text-sm font-bold leading-tight text-ink-soft">{label}</div>
      </div>
    </Card>
  );
}
