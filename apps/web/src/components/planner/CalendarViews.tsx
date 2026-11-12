"use client";
import { useState } from "react";
import { Button, cn, Icon } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { addDays, formatDay, fromISO, startOfWeek, toISO, todayISO, weekdayName } from "@/lib/planDates";
import { getMonth, getWeek, type DayOut, type TaskOut } from "@/lib/planner";
import { useAsync } from "@/lib/useAsync";
import { DayTasks } from "./DayTasks";
import { KIND_DOT } from "./parts";


const byDay = (list: DayOut[]) => {
  const m = new Map<string, TaskOut[]>();
  for (const x of list) m.set(x.day, [...x.tasks]);
  for (const list of m.values()) list.sort((a, b) => a.position - b.position);
  return m;
};

function Nav({ label, onPrev, onNext, onToday }: { label: string; onPrev: () => void; onNext: () => void; onToday: () => void }) {
  const t = useT();
  return (
    <div className="flex items-center justify-between gap-2">
      <Button variant="secondary" onClick={onPrev} aria-label={t("plan.prev")} className="px-4">
        <Icon name="chevron-left" size={20} />
      </Button>
      <button type="button" onClick={onToday} className="min-w-0 truncate rounded-xl px-2 py-1 text-lg font-extrabold" title={t("plan.thisPeriod")}>
        {label}
      </button>
      <Button variant="secondary" onClick={onNext} aria-label={t("plan.next")} className="px-4">
        <Icon name="chevron-right" size={20} />
      </Button>
    </div>
  );
}

export function WeekView() {
  const { locale } = useLocale();
  const [start, setStart] = useState(() => startOfWeek(todayISO()));
  const end = addDays(start, 6);
  const range = useAsync(() => getWeek(start), [start]);
  return (
    <div className="flex flex-col gap-4">
      <Nav
        label={`${formatDay(start, locale, { day: "numeric", month: "short" })} – ${formatDay(end, locale, { day: "numeric", month: "short" })}`}
        onPrev={() => setStart(addDays(start, -7))}
        onNext={() => setStart(addDays(start, 7))}
        onToday={() => setStart(startOfWeek(todayISO()))}
      />
      <AsyncView state={range.state} onRetry={range.reload}>
        {(r) => {
          const days = byDay(r.days);
          return (
            <div className="flex flex-col gap-4">
              {Array.from({ length: 7 }, (_, i) => addDays(start, i)).map((d) => (
                <DayTasks key={d} day={d} tasks={days.get(d) ?? []} />
              ))}
            </div>
          );
        }}
      </AsyncView>
    </div>
  );
}

export function MonthView() {
  const t = useT();
  const { locale } = useLocale();
  const today = todayISO();
  const [first, setFirst] = useState(() => `${today.slice(0, 7)}-01`);
  const [selected, setSelected] = useState(today);
  const gridStart = startOfWeek(first);
  const gridEnd = addDays(gridStart, 41);
  const month = first.slice(0, 7);
  const range = useAsync(() => getMonth(Number(month.slice(0, 4)), Number(month.slice(5, 7))), [month]);
  const shift = (n: number) => {
    const d = fromISO(first);
    d.setMonth(d.getMonth() + n, 1);
    setFirst(toISO(d));
  };
  return (
    <div className="flex flex-col gap-4">
      <Nav
        label={formatDay(first, locale, { month: "long", year: "numeric" })}
        onPrev={() => shift(-1)}
        onNext={() => shift(1)}
        onToday={() => {
          setFirst(`${today.slice(0, 7)}-01`);
          setSelected(today);
        }}
      />
      <div className="grid grid-cols-7 gap-1 text-center text-xs font-extrabold uppercase text-ink-soft" aria-hidden="true">
        {Array.from({ length: 7 }, (_, i) => (
          <span key={i}>{weekdayName(i, locale)}</span>
        ))}
      </div>
      <AsyncView state={range.state} onRetry={range.reload}>
        {(range) => {
          const days = byDay(range.days);
          return (
            <>
              <div className="grid grid-cols-7 gap-1">
                {Array.from({ length: 42 }, (_, i) => addDays(gridStart, i)).map((d) => {
                  const list = days.get(d) ?? [];
                  const taper = !!range.plan_end && d > range.plan_end && d <= range.exam_date;
                  const inMonth = d.slice(0, 7) === first.slice(0, 7);
                  return (
                    <button
                      key={d}
                      type="button"
                      onClick={() => inMonth && setSelected(d)}
                      disabled={!inMonth}
                      aria-pressed={selected === d}
                      aria-label={formatDay(d, locale)}
                      className={cn(
                        "flex aspect-square min-w-0 flex-col items-center justify-between rounded-xl border-2 p-1 text-sm font-extrabold",
                        selected === d ? "border-brand" : "border-line",
                        taper && "bg-accent-soft",
                        d === today && "ring-2 ring-brand",
                        !inMonth && "pointer-events-none opacity-40",
                      )}
                    >
                      <span>{fromISO(d).getDate()}</span>
                      <span className="flex flex-wrap justify-center gap-0.5" aria-hidden="true">
                        {list.slice(0, 3).map((x) => (
                          <span key={x.id} className={cn("size-1.5 rounded-full", x.status === "done" ? "bg-accent-deep" : KIND_DOT[x.kind])} />
                        ))}
                      </span>
                    </button>
                  );
                })}
              </div>
              <p className="flex flex-wrap gap-x-4 gap-y-1 text-xs font-bold text-ink-soft">
                <span className="inline-flex items-center gap-1">
                  <span className="size-3 rounded bg-accent-soft ring-1 ring-accent" />
                  {t("plan.taper")}
                </span>
              </p>
              <DayTasks day={selected} tasks={days.get(selected) ?? []} />
            </>
          );
        }}
      </AsyncView>
    </div>
  );
}
