"use client";
import { useLocale, useT } from "@dtmai/i18n";
import { formatDay } from "@/lib/planDates";
import type { TaskOut } from "@/lib/planner";
import { TaskCard } from "./parts";

/** Tasks of one day. */
export function DayTasks({ day, tasks, showHeading = true }: { day: string; tasks: TaskOut[]; showHeading?: boolean }) {
  const t = useT();
  const { locale } = useLocale();
  const label = formatDay(day, locale, { weekday: "long", day: "numeric", month: "long" });
  return (
    <section className="flex flex-col gap-2" aria-label={label}>
      {showHeading && <h3 className="text-sm uppercase text-ink-soft">{label}</h3>}
      {tasks.length === 0 ? (
        <p className="rounded-card border-2 border-dashed border-line p-3 text-ink-soft">{t("plan.noTasks")}</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {tasks.map((x) => (
            <TaskCard key={x.id} task={x} />
          ))}
        </ul>
      )}
    </section>
  );
}
