"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { PathNode, Tabs, type PathNodeState } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { GoalRing } from "@/components/GoalRing";
import { api, type PathLesson } from "@/lib/api";
import { useLearnLanguage } from "@/lib/auth";
import { contentLang, pick } from "@/lib/localized";
import { useStats } from "@/lib/stats";
import { useAsync } from "@/lib/useAsync";

const OFFSETS = [0, 40, 64, 40, 0, -40, -64, -40];

const nodeState = (l: PathLesson): PathNodeState => (l.progress.state === "done" ? "done" : l.progress.state === "locked" ? "locked" : l.legendary ? "legendary" : "active");

function SubjectPath({ subjectId }: { subjectId: string }) {
  const t = useT();
  const router = useRouter();
  const language = useLearnLanguage();
  const { locale } = useLocale();
  const { state, reload } = useAsync(
    () => api.unwrap(api.client.GET("/v1/catalog/subjects/{subject_id}/path", { params: { path: { subject_id: subjectId }, query: { language, locale: contentLang(locale) } } })),
    [subjectId, language, locale],
  );
  return (
    <AsyncView state={state} onRetry={reload} isEmpty={(d) => d.units.length === 0} emptyText={t("learn.empty")}>
      {(path) => (
        <div className="flex flex-col gap-8">
          {path.units.map((u, ui) => (
            <section key={u.id} className="flex flex-col items-center gap-4">
              <div className="w-full rounded-card bg-green-deep p-4 text-white">
                <p className="text-sm uppercase">
                  {t("learn.unit", { n: ui + 1 })} · {u.progress.completed_lessons}/{u.progress.total_lessons}
                </p>
                <h2 className="text-xl">{u.title}</h2>
              </div>
              {u.lessons.map((l, i) => (
                <div key={l.id} style={{ transform: `translateX(${OFFSETS[i % OFFSETS.length]}px)` }}>
                  <PathNode
                    state={nodeState(l)}
                    label={`${l.title} — ${t(l.progress.state === "done" ? "learn.node.done" : l.progress.state === "locked" ? "learn.node.locked" : "learn.node.start")}`}
                    onClick={() => router.push(`/lesson/${l.id}/`)}
                  />
                </div>
              ))}
            </section>
          ))}
        </div>
      )}
    </AsyncView>
  );
}

export function LearnView() {
  const t = useT();
  const { locale } = useLocale();
  const subjects = useAsync(() => api.unwrap(api.client.GET("/v1/catalog/subjects")), []);
  const stats = useStats();
  const [active, setActive] = useState<string | null>(null);
  return (
    <AsyncView state={subjects.state} onRetry={subjects.reload} isEmpty={(d) => d.length === 0}>
      {(list) => {
        const current = active ?? list[0].id;
        return (
          <div className="flex flex-col gap-6">
            {stats.state.status === "ready" && (
              <div className="flex items-center gap-4 rounded-card border-2 border-line p-3">
                <GoalRing done={stats.state.data.today_xp} goal={stats.state.data.daily_goal_xp} />
                <div>
                  <p className="font-extrabold text-ink">{t("goal.title")}</p>
                  <p className="text-ink-soft">{t("goal.label", { done: stats.state.data.today_xp, goal: stats.state.data.daily_goal_xp })}</p>
                </div>
              </div>
            )}
            <Tabs items={list.map((s) => ({ id: s.id, label: pick(s.names, locale) }))} value={current} onChange={setActive} />
            <SubjectPath subjectId={current} />
          </div>
        );
      }}
    </AsyncView>
  );
}
