import type { ReactNode } from "react";
import { cn } from "../cn";
import { FlameIcon, GemIcon, HeartIcon, XpIcon } from "./icons";

export function StatChip({
  icon,
  value,
  label,
  tone = "text-ink",
  className,
}: {
  icon: ReactNode;
  value: ReactNode;
  label: string;
  tone?: string;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 font-extrabold", tone, className)} title={label}>
      {icon}
      <span>{value}</span>
      <span className="sr-only">{label}</span>
    </span>
  );
}

type V = { value: ReactNode; label: string; className?: string };
export const HeartsStat = (p: V) => <StatChip icon={<HeartIcon />} tone="text-red-deep" {...p} />;
export const GemsStat = (p: V) => <StatChip icon={<GemIcon />} tone="text-[#0d6fa0]" {...p} />;
export const XpStat = (p: V) => <StatChip icon={<XpIcon />} tone="text-gold-deep" {...p} />;
export const StreakStat = (p: V) => <StatChip icon={<FlameIcon />} tone="text-[#b45f00]" {...p} />;
