"use client";
import { cn } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { weekdayName } from "@/lib/planDates";

const WEEK = [0, 1, 2, 3, 4, 5, 6];

/** Implementation intention: "I study at HH:MM on these days". Empty days = every day; empty time = default reminder. */
export function StudyTimeStep({
  time,
  setTime,
  days,
  setDays,
}: {
  time: string;
  setTime: (v: string) => void;
  days: number[];
  setDays: (v: number[]) => void;
}) {
  const t = useT();
  const { locale } = useLocale();
  const toggle = (d: number) => setDays(days.includes(d) ? days.filter((x) => x !== d) : [...days, d].sort((a, b) => a - b));
  return (
    <div className="flex flex-col gap-5">
      <label className="flex flex-col gap-2">
        <span className="font-extrabold">{t("plan.wizard.study.time")}</span>
        <input
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          className="w-40 rounded-xl border-2 border-line bg-white px-3 py-2 text-xl font-extrabold tabular-nums"
        />
      </label>
      <fieldset className="flex flex-col gap-2">
        <legend className="font-extrabold">{t("plan.wizard.study.days")}</legend>
        <div className="flex flex-wrap gap-2">
          {WEEK.map((d) => (
            <button
              key={d}
              type="button"
              aria-pressed={days.includes(d)}
              onClick={() => toggle(d)}
              className={cn(
                "min-w-12 rounded-xl border-2 px-3 py-2 text-sm font-extrabold uppercase",
                days.includes(d) ? "border-brand bg-brand text-white" : "border-line bg-white text-ink",
              )}
            >
              {weekdayName(d, locale)}
            </button>
          ))}
        </div>
      </fieldset>
      <p className="text-sm text-ink-soft">{t("plan.wizard.study.hint")}</p>
    </div>
  );
}
