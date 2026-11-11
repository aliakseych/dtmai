"use client";
import Link from "next/link";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { buttonClass, Mascot } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { PageTitle } from "@/components/PageTitle";
import { ProgressRing, TaskCard } from "@/components/planner/parts";
import { QuestItem } from "@/components/quests/QuestItem";
import { api } from "@/lib/api";
import { formatDay } from "@/lib/planDates";
import { getHome, getToday } from "@/lib/planner";
import { useAsync } from "@/lib/useAsync";
import { useCountdown } from "@/lib/useCountdown";
import { AnalyticsCard } from "./AnalyticsCard";
import { DailyQuestions } from "./DailyQuestions";

const getQuests = () => api.unwrap(api.client.GET("/v1/gamification/quests"));

export function HomeView() {
  const t = useT();
  return (
    <>
      <PageTitle>{t("home.title")}</PageTitle>
      <div className="flex flex-col gap-5">
        <Hero />
        <DailyQuestions />
        <Quests />
        <TodayPlan />
        <AnalyticsCard />
      </div>
    </>
  );
}

function Hero() {
  const t = useT();
  const { locale } = useLocale();
  const home = useAsync(getHome, []);
  const h = home.state.status === "ready" ? home.state.data : null;
  const examDate = h?.exam_date ?? null;
  const reduce = useReducedMotion();
  const left = useCountdown(examDate ? `${examDate}T00:00:00+05:00` : null);
  const value = h?.predicted_score ?? 0;
  const max = h?.max_score ?? null;
  const units: [number, string][] = [
    [Math.floor(left / 86400), t("home.d")],
    [Math.floor((left % 86400) / 3600), t("home.h")],
    [Math.floor((left % 3600) / 60), t("home.m")],
    [left % 60, t("home.s")],
  ];
  return (
    <section className="flex flex-col gap-4 rounded-card border-2 border-line bg-white p-4 sm:flex-row sm:items-center">
      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <h2 className="text-sm uppercase text-ink-soft">{t("home.countdown")}</h2>
        {examDate ? (
          <>
            <div className="grid grid-cols-4 gap-2" role="timer" aria-label={t("home.countdown")}>
              {units.map(([n, l]) => (
                <div key={l} className="min-w-0 rounded-xl bg-brand py-2 text-center text-white">
                  <div className="relative h-8 overflow-hidden">
                    <AnimatePresence initial={false} mode="popLayout">
                      <motion.div
                        key={n}
                        initial={reduce ? false : { y: -16, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={reduce ? undefined : { y: 16, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="text-2xl font-extrabold leading-8 tabular-nums"
                      >
                        {String(n).padStart(2, "0")}
                      </motion.div>
                    </AnimatePresence>
                  </div>
                  <div className="text-xs font-bold uppercase opacity-80">{l}</div>
                </div>
              ))}
            </div>
            <p className="text-sm text-ink-soft">{formatDay(examDate, locale, { day: "numeric", month: "long", year: "numeric" })}</p>
          </>
        ) : (
          <p className="text-ink-soft">{t("home.noDate")}</p>
        )}
      </div>
      <div className="flex flex-col items-center gap-1 self-center">
        <ProgressRing value={value} max={max ?? Math.max(value, 1)} size={132} stroke={12}>
          <span className="text-2xl font-extrabold tabular-nums">{Math.round(value)}</span>
          {max !== null && <span className="text-xs font-bold text-ink-soft">/ {max}</span>}
        </ProgressRing>
        <span className="text-sm font-bold">{t("home.predicted")}</span>
        {max === null && (
          <Link href="/plan/setup/" className="text-sm font-extrabold text-blue-deep underline">
            {t("home.setField")}
          </Link>
        )}
      </div>
    </section>
  );
}

function Quests() {
  const t = useT();
  const { state, reload } = useAsync(getQuests, []);
  return (
    <section className="flex flex-col gap-2" aria-label={t("home.quests")}>
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg">{t("home.quests")}</h2>
        <Link href="/quests/" className="text-sm font-extrabold text-blue-deep">
          {t("home.all")}
        </Link>
      </div>
      <AsyncView state={state} onRetry={reload} isEmpty={(d) => d.length === 0} emptyText={t("quests.empty")}>
        {(quests) => (
          <ul className="flex flex-col gap-2">
            {quests.map((q) => (
              <QuestItem key={q.id} quest={q} compact />
            ))}
          </ul>
        )}
      </AsyncView>
    </section>
  );
}

function TodayPlan() {
  const t = useT();
  const today = useAsync(getToday, []);
  return (
    <section className="flex flex-col gap-2" aria-label={t("home.today")}>
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg">{t("home.today")}</h2>
        <Link href="/plan/" className="text-sm font-extrabold text-blue-deep">
          {t("home.openPlan")}
        </Link>
      </div>
      <AsyncView state={today.state} onRetry={today.reload}>
        {(d) =>
          d === null ? (
            <div className="flex flex-col items-center gap-3 rounded-card border-2 border-line bg-white p-5 text-center">
              <Mascot mood="wave" size={96} alt="" className="h-auto w-20" />
              <p className="font-bold">{t("plan.empty.body")}</p>
              <Link href="/plan/setup/" className={buttonClass("primary", true)}>
                {t("plan.generate")}
              </Link>
            </div>
          ) : d.rest_day && d.tasks.length === 0 ? (
            <p className="rounded-card border-2 border-line bg-white p-4 font-bold">{t("plan.restBody")}</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {d.tasks.map((task) => (
                <TaskCard key={task.id} task={task} />
              ))}
            </ul>
          )
        }
      </AsyncView>
    </section>
  );
}
