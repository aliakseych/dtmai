"use client";
import type { ReactNode } from "react";
import type { LearnerStats } from "./types";

function Kpi({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="rounded-xl border-2 border-line bg-white p-3">
      <div className="text-[11px] font-extrabold uppercase tracking-wide text-ink-soft">{label}</div>
      <div className="mt-0.5 text-2xl font-extrabold tabular-nums text-blue-deep">{value}</div>
      {hint && <div className="text-[11px] font-semibold text-ink-soft">{hint}</div>}
    </div>
  );
}

/** XP, streaks, lessons and accuracy in a responsive grid (2 cols on phones, 5 on wide). */
export function KpiRow({ stats }: { stats: Pick<LearnerStats, "xp_total" | "streak_current" | "streak_best" | "lessons_completed" | "accuracy"> }) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-5">
      <Kpi label="XP" value={stats.xp_total.toLocaleString("en")} />
      <Kpi label="Streak" value={stats.streak_current} hint="days, current" />
      <Kpi label="Best streak" value={stats.streak_best} hint="days" />
      <Kpi label="Lessons" value={stats.lessons_completed} hint="completed" />
      <Kpi label="Accuracy" value={`${Math.round(stats.accuracy * 100)}%`} hint="all time" />
    </div>
  );
}
