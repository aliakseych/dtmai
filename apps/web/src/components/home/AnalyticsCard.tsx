"use client";
import Link from "next/link";
import { buttonClass, Card, Mascot } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { useBilling } from "@/lib/billing";
import { getAnalytics, type AnalyticsOut } from "@/lib/planner";
import { useAsync } from "@/lib/useAsync";

/** Pro analytics: hidden while payments are off; blurred behind a lock for non-premium users. */
export function AnalyticsCard() {
  const { paymentsEnabled, canBuy } = useBilling();
  if (!paymentsEnabled) return null;
  return <Loaded canBuy={canBuy} />;
}

function Loaded({ canBuy }: { canBuy: boolean }) {
  const t = useT();
  const { state, reload } = useAsync(getAnalytics, []);
  return (
    <section className="flex flex-col gap-2" aria-label={t("analytics.title")}>
      <h2 className="text-lg">{t("analytics.title")}</h2>
      <AsyncView state={state} onRetry={reload}>
        {(a) => (a.locked ? <Locked canBuy={canBuy} /> : <Stats a={a} />)}
      </AsyncView>
    </section>
  );
}

function Locked({ canBuy }: { canBuy: boolean }) {
  const t = useT();
  return (
    <div className="relative overflow-hidden rounded-card border-2 border-line bg-white">
      <div aria-hidden className="pointer-events-none flex select-none flex-col gap-3 p-4 blur-sm">
        {[80, 55, 35].map((w) => (
          <div key={w} className="h-4 rounded-full bg-brand-soft" style={{ width: `${w}%` }} />
        ))}
      </div>
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-white/60 p-4 text-center">
        <Mascot mood="lock" size={72} alt="" className="h-auto w-16" />
        <p className="font-extrabold">{t("analytics.locked")}</p>
        {canBuy && (
          <Link href="/premium/" className={buttonClass("primary")}>
            {t("analytics.cta")}
          </Link>
        )}
      </div>
    </div>
  );
}

function Stats({ a }: { a: AnalyticsOut }) {
  const t = useT();
  return (
    <Card pad="sm" className="flex flex-col gap-3">
      <dl className="grid grid-cols-2 gap-3">
        <div className="rounded-xl bg-snow p-3">
          <dt className="text-xs font-bold uppercase text-ink-soft">{t("analytics.accuracy")}</dt>
          <dd className="text-2xl font-extrabold">{`${Math.round(a.completion_rate * 100)}%`}</dd>
        </div>
        <div className="rounded-xl bg-snow p-3">
          <dt className="text-xs font-bold uppercase text-ink-soft">{t("analytics.minutes")}</dt>
          <dd className="text-2xl font-extrabold">{a.minutes_done}</dd>
        </div>
      </dl>
      <div>
        <h3 className="text-sm uppercase text-ink-soft">{t("analytics.weak")}</h3>
        {a.mastery.length === 0 ? (
          <p className="text-ink-soft">{t("common.empty")}</p>
        ) : (
          <ul className="mt-1 flex flex-col gap-1">
            {[...a.mastery]
              .sort((x, y) => (x.mastery ?? 0) - (y.mastery ?? 0))
              .map((w) => (
                <li key={w.subject_id} className="flex items-center gap-2">
                  <span className="min-w-0 flex-1 break-words font-bold">{w.subject_name}</span>
                  <span className="h-2 w-20 shrink-0 overflow-hidden rounded-full bg-line" role="img" aria-label={`${Math.round((w.mastery ?? 0) * 100)}%`}>
                    <span className="block h-full bg-accent" style={{ width: `${Math.round((w.mastery ?? 0) * 100)}%` }} />
                  </span>
                </li>
              ))}
          </ul>
        )}
      </div>
    </Card>
  );
}
