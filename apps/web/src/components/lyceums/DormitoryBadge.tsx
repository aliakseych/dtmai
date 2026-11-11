"use client";
import { useT } from "@dtmai/i18n";
import { cn } from "@dtmai/ui";
import type { DormitoryStatus } from "@/lib/api";

const STYLE = {
  available: "border-accent-deep bg-accent-soft text-ink",
  limited: "border-line bg-snow text-ink",
  none: "border-line bg-white text-ink-soft",
} as const;

/** Dormitory availability pill; renders nothing while the status is unknown. */
export function DormitoryBadge({ status, className }: { status?: DormitoryStatus | null; className?: string }) {
  const t = useT();
  if (!status || status === "unknown") return null;
  return (
    <span className={cn("inline-flex items-center rounded-full border-2 px-2.5 py-0.5 text-xs font-extrabold", STYLE[status], className)}>
      {t(`lyceums.dorm.${status}` as const)}
    </span>
  );
}
