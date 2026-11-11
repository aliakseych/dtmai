import type { ReactNode } from "react";
import { Card } from "@dtmai/ui";

/** Compact KPI tile: icon + big value + label. */
export function KpiCard({ icon, value, label, className }: { icon: ReactNode; value: ReactNode; label: string; className?: string }) {
  return (
    <Card className={`flex min-w-0 items-center gap-3 p-4 ${className ?? ""}`}>
      <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-brand-soft">{icon}</div>
      <div className="min-w-0">
        <div className="truncate text-2xl font-extrabold leading-tight text-ink">{value}</div>
        <div className="truncate text-sm font-bold text-ink-soft">{label}</div>
      </div>
    </Card>
  );
}

/** Brand icon from public/brand/icon-*.png. */
export function BrandIcon({ name, size = 32 }: { name: "streak" | "xp" | "lesson" | "check" | "trophy" | "mock"; size?: number }) {
  return <img src={`/brand/icon-${name}.png`} alt="" width={size} height={size} className="select-none object-contain" draggable={false} />;
}
