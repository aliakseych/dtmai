"use client";
import { useState } from "react";
import { Tabs } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { GoalRing } from "@/components/GoalRing";
import { api } from "@/lib/api";
import { pick } from "@/lib/localized";
import { useStats } from "@/lib/stats";
import { useAsync } from "@/lib/useAsync";
import { useAuth } from "@/lib/auth";
import { SubjectPath } from "./SubjectPath";
import { DreamPin } from "./DreamPin";

const LAST = "dtmai.learn.subject";

export function LearnView() {
  const t = useT();
  const { locale } = useLocale();
  const subjects = useAsync(() => api.unwrap(api.client.GET("/v1/catalog/subjects")), []);
  const stats = useStats();
  const { me } = useAuth();
  const [picked, setPicked] = useState<string | null>(() => {
    try {
      return window.localStorage.getItem(LAST) ?? null;
    } catch {
      return null;
    }
  });
  const choose = (id: string) => {
    setPicked(id);
    try {
      window.localStorage.setItem(LAST, id);
    } catch {
      /* storage unavailable */
    }
  };
  return (
    <AsyncView state={subjects.state} onRetry={subjects.reload} isEmpty={(d) => d.length === 0}>
      {(all) => {
        // The learner's chosen subjects lead; the rest stay reachable after them.
        const mine = me?.subject_ids ?? [];
        const list = [...all].sort((a, b) => Number(!mine.includes(a.id)) - Number(!mine.includes(b.id)));
        const fallback = list[0]!.id;
        const current = list.some((x) => x.id === picked) ? picked! : fallback;
        return (
          <div className="flex flex-col gap-6">
            <DreamPin />
            <Tabs items={list.map((s) => ({ id: s.id, label: pick(s.names, locale) }))} value={current} onChange={choose} />
            {stats.state.status === "ready" && (
              <div className="flex items-center gap-4 rounded-card border-2 border-line p-3">
                <GoalRing done={stats.state.data.today_xp} goal={stats.state.data.daily_goal_xp} />
                <div>
                  <p className="font-extrabold text-ink">{t("goal.title")}</p>
                  <p className="text-ink-soft">{t("goal.label", { done: stats.state.data.today_xp, goal: stats.state.data.daily_goal_xp })}</p>
                </div>
              </div>
            )}
            <SubjectPath subjectId={current} />
          </div>
        );
      }}
    </AsyncView>
  );
}
