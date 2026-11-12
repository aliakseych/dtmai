"use client";
import { useT } from "@dtmai/i18n";
import { Badge, type BadgeTone } from "@dtmai/ui";
import type { DormitoryStatus } from "@/lib/api";

const TONE: Record<Exclude<DormitoryStatus, "unknown">, BadgeTone> = { available: "accent", limited: "neutral", none: "outline" };

/** Dormitory availability pill; renders nothing while the status is unknown. */
export function DormitoryBadge({ status, className }: { status?: DormitoryStatus | null; className?: string }) {
  const t = useT();
  if (!status || status === "unknown") return null;
  return (
    <Badge tone={TONE[status]} className={className}>
      {t(`lyceums.dorm.${status}` as const)}
    </Badge>
  );
}
