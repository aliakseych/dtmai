"use client";
import Link from "next/link";
import { useState } from "react";
import { Badge, buttonClass, Card, EmptyState, Tabs } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { useGoogleClientId } from "@/components/auth/GoogleSignIn";
import { useAuth } from "@/lib/auth";
import { PageTitle } from "@/components/PageTitle";
import { getHome, getProfile, getSettings, getToday, type HomeOut, type TodayOut } from "@/lib/planner";
import { formatDay, todayISO } from "@/lib/planDates";
import { useAsync } from "@/lib/useAsync";
import { WeekView, MonthView } from "./CalendarViews";
import { ProgressRing, TaskCard } from "./parts";

type Tab = "focus" | "week" | "month";

/** `/plan`: Focus (today), Week and Month. Without a plan it offers the wizard. */
export function PlanView() {
  const t = useT();
  const { isGuest } = useAuth();
  const google = useGoogleClientId();
  const plan = useAsync(getSettings, []);
  const [tab, setTab] = useState<Tab>("focus");
  const home = useAsync(getHome, []);
  return (
    <>
      <PageTitle>{t("plan.title")}</PageTitle>
      {isGuest && (
        <Card className="mb-5 flex flex-col items-center gap-3 text-center">
          <h2 className="text-xl">{t("account.gate.title")}</h2>
          <p className="text-ink-soft">{t(google ? "account.gate.body" : "account.gate.body.noGoogle")}</p>
          <Link href="/account/" className={buttonClass("primary", true, "min-h-11")}>
            {t("account.gate.cta")}
          </Link>
        </Card>
      )}
      <AsyncView state={plan.state} onRetry={plan.reload}>
        {(p) =>
          p === null ? (
            <NoPlan />
          ) : (
            <div className="flex flex-col gap-5">
              <AsyncView state={home.state} onRetry={home.reload}>{(h) => <HeaderBody h={h} directionCode={p.direction_code} examDate={p.exam_date} />}</AsyncView>
              <Tabs
                items={[
                  { id: "focus", label: t("plan.view.focus") },
                  { id: "week", label: t("plan.view.week") },
                  { id: "month", label: t("plan.view.month") },
                ]}
                value={tab}
                onChange={setTab}
              />
              {tab === "focus" && <FocusView onDone={home.reload} />}
              {tab === "week" && <WeekView />}
              {tab === "month" && <MonthView />}
              <Link href="/plan/setup/" className={buttonClass("ghost", true)}>
                {t("plan.edit")}
              </Link>
            </div>
          )
        }
      </AsyncView>
    </>
  );
}

export function NoPlan() {
  const t = useT();
  return (
    <EmptyState
      mood="calendar"
      title={t("plan.empty.title")}
      body={t("plan.empty.body")}
      action={
        <Link href="/plan/setup/" className={buttonClass("primary")}>
          {t("plan.generate")}
        </Link>
      }
    />
  );
}

function HeaderBody({ h, directionCode, examDate }: { h: HomeOut; directionCode: string; examDate: string }) {
  const t = useT();
  const { locale } = useLocale();
  // The date is "approximate" while the official exam date is unconfirmed and the learner kept it.
  const profile = useAsync(() => getProfile(directionCode).catch(() => null), [directionCode]);
  const approx = profile.state.status === "ready" && profile.state.data !== null && !profile.state.data.date_verified && profile.state.data.exam_date === examDate;
  return (
    <Card pad="sm" className="flex items-center gap-4">
      <ProgressRing value={h.today_done} max={Math.max(1, h.today_total)} size={84} stroke={9} label={t("plan.todayProgress", { done: h.today_done, total: h.today_total })}>
        <span className="text-lg font-extrabold leading-none">{h.today_total > 0 ? Math.round((h.today_done / h.today_total) * 100) : 0}%</span>
      </ProgressRing>
      <div className="min-w-0">
        <p className="text-xl font-extrabold">{t("plan.daysLeft", { n: h.days_left ?? 0 })}</p>
        <p className="flex flex-wrap items-center gap-2 text-sm font-bold text-ink-soft">
          <span>{formatDay(examDate, locale, { day: "numeric", month: "long", year: "numeric" })}</span>
          {approx && <Badge>{t("exam.approximate")}</Badge>}
        </p>
        <p className="text-sm text-ink-soft">{t("plan.todayProgress", { done: h.today_done, total: h.today_total })}</p>
      </div>
    </Card>
  );
}

function FocusView({ onDone }: { onDone: () => void }) {
  const today = useAsync(getToday, []);
  const changed = () => {
    today.reload();
    onDone();
  };
  return (
    <AsyncView state={today.state} onRetry={today.reload}>
      {(d) => (d === null ? <NoPlan /> : <FocusBody d={d} onDone={changed} />)}
    </AsyncView>
  );
}

function FocusBody({ d, onDone }: { d: TodayOut; onDone: () => void }) {
  const t = useT();
  const { locale } = useLocale();
  const done = d.tasks.filter((x) => x.status === "done").length;
  return (
    <div className="flex flex-col gap-5">
      <h2 className="text-xl">{formatDay(todayISO(), locale, { weekday: "long", day: "numeric", month: "long" })}</h2>
      {d.rest_day && d.tasks.length === 0 ? (
        <Card pad="none">
          <EmptyState mood="sleep" title={t("plan.rest")} body={t("plan.restBody")} />
        </Card>
      ) : d.tasks.length === 0 ? (
        <EmptyState compact title={t("plan.noTasks")} />
      ) : (
        <section className="flex flex-col gap-2" aria-label={t("plan.today")}>
          <p className="text-sm font-extrabold uppercase text-ink-soft">{t("plan.todayProgress", { done, total: d.tasks.length })}</p>
          <ul className="flex flex-col gap-2">
            {d.tasks.map((x) => (
              <TaskCard key={x.id} task={x} onDone={onDone} />
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
