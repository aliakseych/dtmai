"use client";
import Link from "next/link";
import type { ReactNode } from "react";
import { Card, Mascot, buttonClass } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { Reveal } from "@/components/motion/Reveal";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { AccuracyRing } from "./AccuracyRing";
import { ActivityBars } from "./ActivityBars";
import { BrandIcon, KpiCard } from "./KpiCard";
import { MockHistoryChart } from "./MockHistoryChart";
import { StreakHeatmap } from "./StreakHeatmap";
import { SubjectMastery } from "./SubjectMastery";
import type { Stats } from "./types";

const isEmpty = (s: Stats) => s.xp_total === 0 && s.lessons_completed === 0 && s.mocks.length === 0 && s.daily.every((d) => d.answered === 0);

function Panel({ title, delay, children }: { title: string; delay: number; children: ReactNode }) {
  return (
    <Reveal delay={delay} y={16} className="min-w-0">
      <Card className="flex h-full min-w-0 flex-col gap-3">
        <h3 className="text-lg">{title}</h3>
        {children}
      </Card>
    </Reveal>
  );
}

/** Learner statistics: KPIs, 30-day activity, calendar, subject mastery and mock history. */
export function StatsSection() {
  const t = useT();
  const stats = useAsync(() => api.unwrap(api.client.GET("/v1/learning/me/stats")), []);
  const subjects = useAsync(() => api.unwrap(api.client.GET("/v1/catalog/subjects")), []);
  const subjectList = subjects.state.status === "ready" ? subjects.state.data : [];

  return (
    <section aria-labelledby="profile-stats" className="flex min-w-0 flex-col gap-3">
      <h2 id="profile-stats" className="text-xl">
        {t("profile.stats.title")}
      </h2>
      <AsyncView state={stats.state} onRetry={stats.reload}>
        {(s) =>
          isEmpty(s) ? (
            <Reveal>
              <Card className="flex flex-col items-center gap-3 py-8 text-center">
                <Mascot mood="thinking" size={140} alt="" className="h-auto w-28" />
                <h3 className="text-lg">{t("profile.stats.empty.title")}</h3>
                <p className="max-w-sm text-ink-soft">{t("profile.stats.empty.text")}</p>
                <Link href="/learn/" className={buttonClass("primary")}>
                  {t("profile.stats.empty.cta")}
                </Link>
              </Card>
            </Reveal>
          ) : (
            <div className="flex min-w-0 flex-col gap-3">
              <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
                {[
                  <KpiCard key="xp" icon={<BrandIcon name="xp" />} value={s.xp_total} label={t("stat.xp")} />,
                  <KpiCard key="cur" icon={<BrandIcon name="streak" />} value={s.streak_current} label={t("profile.stats.streakCurrent")} />,
                  <KpiCard key="best" icon={<BrandIcon name="trophy" />} value={s.streak_best} label={t("profile.stats.streakBest")} />,
                  <KpiCard key="les" icon={<BrandIcon name="lesson" />} value={s.lessons_completed} label={t("profile.stats.lessons")} />,
                  <KpiCard
                    key="acc"
                    className="col-span-2 md:col-span-1"
                    icon={<AccuracyRing value={s.accuracy} />}
                    value={`${Math.round(s.accuracy * 100)}%`}
                    label={t("profile.stats.accuracy")}
                  />,
                ].map((card, i) => (
                  <Reveal key={card.key} delay={i * 0.06} y={12} className="min-w-0">
                    {card}
                  </Reveal>
                ))}
              </div>
              <div className="grid min-w-0 grid-cols-1 gap-3 xl:grid-cols-2">
                <Panel title={t("profile.stats.activity")} delay={0}>
                  <ActivityBars daily={s.daily} />
                </Panel>
                <Panel title={t("profile.stats.calendar")} delay={0.06}>
                  <StreakHeatmap daily={s.daily} />
                </Panel>
                {s.by_subject.length > 0 && (
                  <Panel title={t("profile.stats.mastery")} delay={0}>
                    <SubjectMastery rows={s.by_subject} subjects={subjectList} />
                  </Panel>
                )}
                <Panel title={t("profile.stats.mocks")} delay={0.06}>
                  {s.mocks.length > 0 ? (
                    <MockHistoryChart mocks={s.mocks} />
                  ) : (
                    <div className="flex flex-col items-center gap-2 py-6 text-center">
                      <BrandIcon name="mock" size={48} />
                      <p className="text-ink-soft">{t("profile.stats.mocksEmpty")}</p>
                      <Link href="/mocks/" className={buttonClass("secondary")}>
                        {t("profile.stats.mocksCta")}
                      </Link>
                    </div>
                  )}
                </Panel>
              </div>
            </div>
          )
        }
      </AsyncView>
    </section>
  );
}
