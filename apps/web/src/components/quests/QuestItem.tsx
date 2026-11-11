"use client";
import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import { cn, GemsStat, ProgressBar, XpStat } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import type { Quest } from "@/lib/api";
import { pick } from "@/lib/localized";

/** Where executing a quest happens; `#current` makes the learn path scroll to the next open lesson. */
export function questHref(action: Quest["action"]): string {
  switch (action) {
    case "lesson":
      return "/learn/#current";
    case "drill":
      return "/practice/run/?kind=drill";
    case "review":
      return "/practice/run/?kind=review";
    case "mock":
      return "/mocks/";
    default:
      return "/learn/";
  }
}

const Chevron = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="m9 6 6 6-6 6" />
  </svg>
);

/** One quest as a card: the whole card starts it; completed quests are inert with a check. */
export function QuestItem({ quest: q, compact = false }: { quest: Quest; compact?: boolean }) {
  const t = useT();
  const { locale } = useLocale();
  const reduce = useReducedMotion();
  const title = pick(q.title, locale);
  const body = (
    <>
      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <h2 className={compact ? "text-base" : "text-lg"}>{title}</h2>
        <ProgressBar value={Math.min(q.progress, q.target)} max={q.target} color="bg-gold" label={title} />
        {!compact && (
          <div className="flex gap-4">
            <GemsStat value={`+${q.reward_gems}`} label={t("stat.gems")} />
            {q.reward_xp > 0 && <XpStat value={`+${q.reward_xp}`} label={t("stat.xp")} />}
          </div>
        )}
      </div>
      {q.completed ? (
        <span className="shrink-0 rounded-full bg-green-soft px-3 py-1 text-sm font-extrabold text-[#2f6200]">✓ {t("quests.done")}</span>
      ) : (
        <span className="flex shrink-0 items-center gap-1 text-sm font-extrabold uppercase text-brand">
          {!compact && t("quests.start")}
          <Chevron />
        </span>
      )}
    </>
  );
  const base = "flex items-center gap-4 rounded-card border-2 border-line p-4";
  if (q.completed) return <li className={cn(base, "opacity-80")}>{body}</li>;
  return (
    <li>
      <motion.div whileHover={reduce ? undefined : { y: -2 }} whileTap={reduce ? undefined : { scale: 0.98 }}>
        <Link href={questHref(q.action)} aria-label={`${t("quests.start")}: ${title}`} className={cn(base, "border-b-4 transition-colors hover:border-brand hover:bg-snow")}>
          {body}
        </Link>
      </motion.div>
    </li>
  );
}
