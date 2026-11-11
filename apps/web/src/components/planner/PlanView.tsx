"use client";
import Link from "next/link";
import { useState } from "react";
import { buttonClass, Mascot, Tabs } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { PageTitle } from "@/components/PageTitle";
import { getHome, getSettings, getToday, type HomeOut, type TodayOut } from "@/lib/planner";
import { formatDay, todayISO } from "@/lib/planDates";
import { useAsync } from "@/lib/useAsync";
import { WeekView, MonthView } from "./CalendarViews";
import { ProgressRing, TaskCard } from "./parts";

type Tab = "focus" | "week" | "month";

/** `/plan`: Focus (today), Week and Month. Without a plan it offers the wizard. */
export function PlanView() {
  const t = useT();
  const plan = useAsync(getSettings, []);
  const [tab, setTab] = useState<Tab>("focus");
  const home = useAsync(getHome, []);
  return (
    <>
      <PageTitle>{t("plan.title")}</PageTitle>
      <AsyncView state={plan.state} onRetry={plan.reload}>
        {(p) =>
          p === null ? (
            <NoPlan />
          ) : (
            <div className="flex flex-col gap-5">
              <AsyncView state={home.state} onRetry={home.reload}>{(h) => <HeaderBody h={h} />}</AsyncView>
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
    <div className="flex flex-col items-center gap-3 py-10 text-center">
      <Mascot mood="wave" size={120} alt="" className="h-auto w-24" />
      <p className="text-lg font-extrabold">{t("plan.empty.title")}</p>
      <p className="text-ink-soft">{t("plan.empty.body")}</p>
      <Link href="/plan/setup/" className={buttonClass("primary")}>
        {t("plan.generate")}
      </Link>
    </div>
  );
}

function HeaderBody({ h }: { h: HomeOut }) {
  const t = useT();
  return (
    <div className="flex items-center gap-4 rounded-card border-2 border-line bg-white p-4">
      <ProgressRing value={h.today_done} max={Math.max(1, h.today_total)} size={84} stroke={9}>
        <span className="text-lg font-extrabold leading-none">{h.today_total > 0 ? Math.round((h.today_done / h.today_total) * 100) : 0}%</span>
      </ProgressRing>
      <div className="min-w-0">
        <p className="text-xl font-extrabold">{t("plan.daysLeft", { n: h.days_left ?? 0 })}</p>
        <p className="text-sm text-ink-soft">
          {h.today_done}/{h.today_total}
        </p>
      </div>
    </div>
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
        <div className="flex flex-col items-center gap-2 rounded-card border-2 border-line bg-white py-8 text-center">
          <Mascot mood="sleep" size={120} alt="" className="h-auto w-24" />
          <p className="text-lg font-extrabold">{t("plan.rest")}</p>
          <p className="text-ink-soft">{t("plan.restBody")}</p>
        </div>
      ) : d.tasks.length === 0 ? (
        <p className="rounded-card border-2 border-dashed border-line p-4 text-center text-ink-soft">{t("plan.noTasks")}</p>
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
