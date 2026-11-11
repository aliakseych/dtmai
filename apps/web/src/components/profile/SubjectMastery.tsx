"use client";
import { motion, useReducedMotion } from "motion/react";
import { useLocale, useT } from "@dtmai/i18n";
import type { Subject } from "@/lib/api";
import { pick } from "@/lib/localized";
import type { Stats } from "./types";

/** One animated mastery bar per subject; names come from the catalog. */
export function SubjectMastery({ rows, subjects }: { rows: Stats["by_subject"]; subjects: Subject[] }) {
  const t = useT();
  const { locale } = useLocale();
  const reduce = useReducedMotion();
  return (
    <ul className="flex max-h-80 flex-col gap-4 overflow-y-auto pr-1">
      {rows.map((r, i) => {
        const name = pick(subjects.find((s) => s.id === r.subject_id)?.names, locale);
        const pct = r.mastery === null ? 0 : Math.round(r.mastery * 100);
        return (
          <li key={r.subject_id} className="flex flex-col gap-1.5">
            <div className="flex items-baseline justify-between gap-3">
              <span className="min-w-0 truncate font-extrabold text-ink">{name}</span>
              <span className="shrink-0 text-sm font-bold text-ink-soft">{r.mastery === null ? t("profile.stats.masteryUnknown") : `${pct}%`}</span>
            </div>
            <div role="progressbar" aria-label={name} aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct} className="h-4 w-full overflow-hidden rounded-full bg-line">
              <motion.div
                className="h-full rounded-full bg-brand"
                initial={{ width: reduce ? `${pct}%` : 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: reduce ? 0 : 0.8, delay: reduce ? 0 : i * 0.08, ease: "easeOut" }}
              />
            </div>
            <span className="text-xs font-bold text-ink-soft">{t("profile.stats.answers", { correct: r.correct, answered: r.answered })}</span>
          </li>
        );
      })}
    </ul>
  );
}
