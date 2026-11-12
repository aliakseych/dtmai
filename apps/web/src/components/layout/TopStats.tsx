"use client";
import { useState } from "react";
import Link from "next/link";
import { buttonClass, GemsStat, HeartsStat, Modal, Skeleton, StreakStat } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { tPlural } from "@/lib/plural";
import { useStats } from "@/lib/stats";
import { clock, useCountdown } from "@/lib/useCountdown";
import { useBilling } from "@/lib/billing";

export function TopStats() {
  const t = useT();
  const { locale } = useLocale();
  const { canBuy } = useBilling();
  const { state } = useStats();
  const [open, setOpen] = useState<"hearts" | "streak" | null>(null);
  const stats = state.status === "ready" ? state.data : null;
  const left = useCountdown(stats?.hearts.next_refill_at);
  if (!stats) return state.status === "error" ? null : <Skeleton className="h-10 w-32 sm:w-48" />;
  const h = stats.hearts;
  return (
    <>
      <div className="flex h-10 items-center gap-1 sm:gap-2">
        <StreakStat value={stats.streak} label={t("stat.streak")} onClick={() => setOpen("streak")} />
        <GemsStat value={stats.gems} label={t("stat.gems")} />
        <HeartsStat value={h.unlimited ? "∞" : h.count} label={t("stat.hearts")} onClick={() => setOpen("hearts")} />
      </div>
      <Modal open={open === "hearts"} onClose={() => setOpen(null)} title={t("stat.hearts")}>
        <p className="mb-2 text-ink-soft">{h.unlimited ? t("hearts.unlimited") : t("hearts.count", { n: h.count, max: h.max })}</p>
        {!h.unlimited && h.count < h.max && h.next_refill_at && <p className="mb-2 font-bold">{t("hearts.nextIn", { time: clock(left) })}</p>}
        <p className="mb-4 text-ink-soft">{t("hearts.hint")}</p>
        <div className="flex flex-col gap-2">
          <Link href="/practice/run/?kind=review" onClick={() => setOpen(null)} className={buttonClass("primary", true)}>
            {t("hearts.earn")}
          </Link>
          {canBuy && (
            <Link href="/premium/" onClick={() => setOpen(null)} className={buttonClass("super", true)}>
              {t("hearts.premium")}
            </Link>
          )}
          <button type="button" className={buttonClass("secondary", true)} onClick={() => setOpen(null)}>
            {t("common.close")}
          </button>
        </div>
      </Modal>
      <Modal open={open === "streak"} onClose={() => setOpen(null)} title={t("stat.streak")}>
        <p className="mb-2 text-xl font-extrabold">{t("stat.days", { n: stats.streak })}</p>
        <p className="mb-2 text-ink-soft">{tPlural(t, locale, "streak.longest", stats.streak_longest)}</p>
        <p className="mb-4 text-ink-soft">{stats.streak_active_today && stats.today_xp >= stats.daily_goal_xp ? t("streak.doneToday") : stats.streak_at_risk ? t("streak.atRisk") : stats.streak_active_today ? tPlural(t, locale, "streak.longest", stats.streak_longest) : t("streak.practice")}</p>
        <button type="button" className={buttonClass("secondary", true)} onClick={() => setOpen(null)}>
          {t("common.close")}
        </button>
      </Modal>
    </>
  );
}
