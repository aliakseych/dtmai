"use client";
import { motion, useReducedMotion } from "motion/react";
import { useLocale, useT } from "@dtmai/i18n";
import type { Stats } from "./types";
import { shortDate, weekdayIndex, weekdayNames } from "./format";

const LEVELS = ["bg-line", "bg-brand/25", "bg-brand/55", "bg-brand"] as const;

/** Calendar-style heatmap (weeks as rows, Monday first) of daily XP; adapted from the library's heatmap-03. */
export function StreakHeatmap({ daily }: { daily: Stats["daily"] }) {
  const t = useT();
  const { locale } = useLocale();
  const reduce = useReducedMotion();
  const first = daily[0];
  if (!first) return null;
  const pad = weekdayIndex(first.date);
  const cells: (Stats["daily"][number] | null)[] = [...Array<null>(pad).fill(null), ...daily];
  while (cells.length % 7) cells.push(null);
  const max = Math.max(1, ...daily.map((d) => d.xp));
  const level = (xp: number) => (xp <= 0 ? 0 : xp <= max / 3 ? 1 : xp <= (2 * max) / 3 ? 2 : 3);
  const active = daily.filter((d) => d.xp > 0).length;

  return (
    <div className="flex flex-col gap-3">
      <div role="img" aria-label={`${t("profile.stats.calendar")}: ${t("stat.days", { n: active })}`} className="mx-auto w-full max-w-sm">
        <div className="mb-1 grid grid-cols-7 gap-1.5 text-center text-xs font-bold text-ink-soft" aria-hidden="true">
          {weekdayNames(locale).map((n) => (
            <span key={n} className="truncate">
              {n}
            </span>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-1.5" aria-hidden="true">
          {cells.map((d, i) =>
            d ? (
              <motion.div
                key={d.date}
                title={`${shortDate(d.date, locale)}: ${d.xp} ${t("stat.xp")}`}
                className={`h-8 rounded-lg ${LEVELS[level(d.xp)]} ${i === pad + daily.length - 1 ? "ring-2 ring-accent-deep ring-offset-1" : ""}`}
                initial={reduce ? false : { opacity: 0, scale: 0.6 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.25, delay: reduce ? 0 : i * 0.012 }}
              />
            ) : (
              <div key={`pad-${i}`} className="h-8" />
            ),
          )}
        </div>
      </div>
      <div className="flex items-center justify-center gap-2 text-xs font-bold text-ink-soft" aria-hidden="true">
        <span>{t("profile.stats.less")}</span>
        {LEVELS.map((c) => (
          <span key={c} className={`h-3.5 w-3.5 rounded ${c}`} />
        ))}
        <span>{t("profile.stats.more")}</span>
      </div>
    </div>
  );
}
