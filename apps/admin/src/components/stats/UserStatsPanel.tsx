"use client";
import { KpiRow } from "./KpiRow";
import { MockHistory } from "./MockHistory";
import { SubjectBars } from "./SubjectBars";
import type { LearnerStats } from "./types";
import { XpChart } from "./XpChart";

/** Full learner statistics view: KPI row, 30-day XP, subject mastery and mock history. */
export function UserStatsPanel({ stats, subjectName }: { stats: LearnerStats; subjectName: (id: string) => string }) {
  return (
    <div className="space-y-4">
      <KpiRow stats={stats} />
      <XpChart daily={stats.daily} />
      <SubjectBars rows={stats.by_subject} subjectName={subjectName} />
      <MockHistory mocks={stats.mocks} />
    </div>
  );
}
