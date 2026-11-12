"use client";
import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import { useT } from "@dtmai/i18n";
import { getDreamGap } from "@/lib/planner";
import { useAsync } from "@/lib/useAsync";

const fmt = (n: number) => String(Math.round(n * 10) / 10);

/** Predicted score vs the dream lyceum's passing score, the gap, the competition ratio and one concrete next step. */
export function GapMeter() {
  const t = useT();
  const reduce = useReducedMotion();
  const { state } = useAsync(getDreamGap, []);
  if (state.status !== "ready" || !state.data.lyceum_id) return null;
  const g = state.data;
  const ratio = g.competition_ratio != null ? t("dream.gap.competition", { ratio: g.competition_ratio.toFixed(1) }) : null;

  if (g.passing_score == null) {
    return (
      <section className="flex flex-col gap-1 rounded-card border-2 border-line bg-white p-4">
        <h2 className="text-sm uppercase text-ink-soft">{t("dream.gap.title")}</h2>
        <p className="font-bold">{t("dream.gap.noBar")}</p>
        {ratio && <p className="text-sm text-ink-soft">{ratio}</p>}
      </section>
    );
  }
  if (g.predicted_score == null) {
    return (
      <section className="flex flex-col gap-2 rounded-card border-2 border-line bg-white p-4">
        <h2 className="text-sm uppercase text-ink-soft">{t("dream.gap.title")}</h2>
        <p className="font-bold">{t("dream.gap.bar", { score: fmt(g.passing_score) })}</p>
        {ratio && <p className="text-sm text-ink-soft">{ratio}</p>}
        <Link href="/plan/setup/" className="inline-flex min-h-11 items-center text-sm font-extrabold text-brand underline">
          {t("dream.gap.noScore")}
        </Link>
      </section>
    );
  }

  const max = g.max_score ?? 146;
  const pct = (n: number) => `${Math.min(100, Math.max(0, (n / max) * 100))}%`;
  const next =
    g.next_points != null && g.next_questions != null
      ? g.weakest_topic_name
        ? t("dream.gap.next", { points: fmt(g.next_points), questions: g.next_questions, topic: g.weakest_topic_name })
        : t("dream.gap.nextPlan", { points: fmt(g.next_points), questions: g.next_questions })
      : null;

  return (
    <section className="flex flex-col gap-3 rounded-card border-2 border-line bg-white p-4">
      <h2 className="text-sm uppercase text-ink-soft">{t("dream.gap.title")}</h2>
      <div
        role="img"
        aria-label={t("dream.gap.aria", { score: fmt(g.predicted_score), bar: fmt(g.passing_score) })}
        className="relative h-4 rounded-full bg-snow"
      >
        <motion.div
          className="absolute inset-y-0 left-0 rounded-full bg-accent"
          initial={reduce ? false : { width: 0 }}
          animate={{ width: pct(g.predicted_score) }}
          transition={{ duration: 0.6 }}
        />
        <div className="absolute -inset-y-1 w-1 rounded bg-brand" style={{ left: pct(g.passing_score) }} />
      </div>
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 text-sm font-bold">
        <span>{t("dream.gap.yours", { score: fmt(g.predicted_score) })}</span>
        <span>{t("dream.gap.bar", { score: fmt(g.passing_score) })}</span>
      </div>
      {g.on_track ? (
        <p className="font-extrabold">{t("dream.gap.onTrack")}</p>
      ) : (
        g.gap != null && <p className="font-extrabold">{t("dream.gap.left", { n: fmt(g.gap) })}</p>
      )}
      {g.milestone && g.next_points != null && (
        <p className="text-sm text-ink-soft">{t("dream.gap.milestone", { n: fmt(g.next_points) })}</p>
      )}
      {ratio && <p className="text-sm text-ink-soft">{ratio}</p>}
      {next ? (
        <Link href="/plan/" className="inline-flex min-h-11 items-center break-words rounded-xl bg-brand-soft px-3 py-2 text-sm font-extrabold text-brand">
          {next}
        </Link>
      ) : (
        !g.on_track && (
          <Link href="/plan/" className="text-sm font-extrabold text-brand underline">
            {t("dream.gap.plan")}
          </Link>
        )
      )}
    </section>
  );
}
