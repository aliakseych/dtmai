import type { ReactNode } from "react";
import { cn } from "../cn";
import { FlameIcon, GemIcon, HeartIcon, XpIcon } from "./icons";

/** Every stat shares the same box (height, padding, icon slot) so a row of them aligns on one baseline. */
const BOX =
  "inline-flex h-10 min-w-14 items-center justify-center gap-1.5 rounded-xl px-2 text-base font-extrabold leading-none tabular-nums";

export function StatChip({
  icon,
  value,
  label,
  tone = "text-ink",
  onClick,
  className,
}: {
  icon: ReactNode;
  value: ReactNode;
  label: string;
  tone?: string;
  /** When set the chip renders as a button with the same box as a static chip. */
  onClick?: () => void;
  className?: string;
}) {
  const inner = (
    <>
      <span aria-hidden className="grid size-6 shrink-0 place-items-center [&>svg]:size-6">
        {icon}
      </span>
      <span className="leading-none">{value}</span>
      <span className="sr-only">{label}</span>
    </>
  );
  if (onClick) {
    return (
      <button type="button" onClick={onClick} title={label} className={cn(BOX, "transition hover:bg-snow", tone, className)}>
        {inner}
      </button>
    );
  }
  return (
    <span className={cn(BOX, tone, className)} title={label}>
      {inner}
    </span>
  );
}

type V = { value: ReactNode; label: string; className?: string; onClick?: () => void };
export const HeartsStat = (p: V) => <StatChip icon={<HeartIcon />} tone="text-red-deep" {...p} />;
export const GemsStat = (p: V) => <StatChip icon={<GemIcon />} tone="text-brand" {...p} />;
export const XpStat = (p: V) => <StatChip icon={<XpIcon />} tone="text-accent-ink" {...p} />;
export const StreakStat = (p: V) => <StatChip icon={<FlameIcon />} tone="text-ink" {...p} />;
