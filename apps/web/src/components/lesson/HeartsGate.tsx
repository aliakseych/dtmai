"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Button, buttonClass, Mascot } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { api, type Stats } from "@/lib/api";
import { pickReviewSubject } from "@/lib/stats";
import { clock, useCountdown } from "@/lib/useCountdown";
import { useBilling } from "@/lib/billing";

/** No dead end when out of hearts: earn them via review (free), wait for the refill, or read about Premium. */
export function HeartsGate({ exitHref, onRetry, subjectId }: { exitHref: string; onRetry?: () => void; subjectId?: string | null }) {
  const t = useT();
  const { canBuy } = useBilling();
  const [stats, setStats] = useState<Stats | null>(null);
  useEffect(() => {
    api.unwrap(api.client.GET("/v1/me/stats")).then(setStats, () => setStats(null));
  }, []);
  // Review earns hearts only where cards are due: use the current subject, else one that has some; none -> just wait.
  const [reviewSubject, setReviewSubject] = useState<string | null | undefined>(subjectId ?? undefined);
  useEffect(() => {
    if (subjectId) return setReviewSubject(subjectId);
    let live = true;
    pickReviewSubject().then(
      (id) => live && setReviewSubject(id),
      () => live && setReviewSubject(null),
    );
    return () => {
      live = false;
    };
  }, [subjectId]);
  const left = useCountdown(stats?.hearts.next_refill_at);
  const refilled = stats !== null && (stats.hearts.count > 0 || (stats.hearts.next_refill_at !== null && left === 0));

  return (
    <div className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-4 px-4 py-10 text-center">
      <Mascot mood="sad" size={200} alt="" className="h-auto w-40" />
      <h1 className="text-3xl">{t("hearts.outTitle")}</h1>
      <p className="text-ink-soft">{t("hearts.outText")}</p>
      <p role="timer" className="rounded-2xl bg-snow px-4 py-2 font-extrabold">
        {refilled ? t("hearts.refilled") : stats?.hearts.next_refill_at ? t("hearts.refillIn", { time: clock(left) }) : t("hearts.waiting")}
      </p>
      {refilled && onRetry && (
        <Button block onClick={onRetry}>
          {t("hearts.tryAgain")}
        </Button>
      )}
      {reviewSubject && (
        <Link href={`/practice/run/?kind=review&subject=${reviewSubject}`} className={buttonClass(refilled ? "secondary" : "primary", true)}>
          {t("hearts.review")}
        </Link>
      )}
      {canBuy && (
        <Link href="/premium/" className={buttonClass("secondary", true)}>
          {t("hearts.premium")}
        </Link>
      )}
      <Link href={exitHref} className={buttonClass("ghost", true)}>
        {t("hearts.back")}
      </Link>
    </div>
  );
}
