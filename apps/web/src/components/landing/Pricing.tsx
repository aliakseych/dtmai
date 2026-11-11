"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { buttonClass, Card, cn } from "@dtmai/ui";
import { useLocale, useT, type MessageKey } from "@dtmai/i18n";
import { api } from "@/lib/api";
import { useBilling } from "@/lib/billing";
import { fmt } from "@/lib/localized";

/** Cheapest monthly premium price from the API; null until loaded or when unavailable. */
function usePremiumPrice(): number | null {
  const [price, setPrice] = useState<number | null>(null);
  useEffect(() => {
    let live = true;
    api
      .unwrap(api.client.GET("/v1/billing/plans"))
      .then((ps) => {
        const paid = ps.filter((p) => p.active && p.code !== "free");
        const monthly = paid.find((p) => p.period_months === 1) ?? paid[0];
        if (live && monthly) setPrice(monthly.price_uzs);
      })
      .catch(() => {});
    return () => {
      live = false;
    };
  }, []);
  return price;
}

function PlanCard({ id, featured, count }: { id: "free" | "premium"; featured?: boolean; count: number }) {
  const t = useT();
  const { locale } = useLocale();
  const { canBuy } = useBilling();
  const price = usePremiumPrice();
  return (
    <Card className={cn("relative flex flex-col gap-4", featured && "border-brand")}>
      {featured && (
        <span className="absolute -top-3 right-4 rounded-full bg-brand px-3 py-1 text-xs font-extrabold uppercase text-white">
          {t("plan.popular")}
        </span>
      )}
      <h3 className="text-2xl">{t(`plan.${id}.name` as MessageKey)}</h3>
      <p className="text-3xl font-extrabold text-ink">
        {id === "free" ? (
          t("common.free")
        ) : (
          <>
            {price !== null ? fmt(locale).format(price) : "—"} <span className="text-base text-ink-soft">{t("common.uzs")} / {t("common.perMonth")}</span>
          </>
        )}
      </p>
      <ul className="flex flex-1 flex-col gap-2 text-ink">
        {Array.from({ length: count }, (_, i) => (
          <li key={i} className="flex gap-2">
            <span className="text-green">✓</span>
            {t(`plan.${id}.f${i + 1}` as MessageKey)}
          </li>
        ))}
      </ul>
      {id === "free" ? (
        <Link href="/onboarding/" className={buttonClass("primary", true)}>
          {t("plan.free.cta")}
        </Link>
      ) : canBuy ? (
        <Link href="/premium/" className={buttonClass("super", true)}>
          {t("plan.premium.cta")}
        </Link>
      ) : (
        <p role="status" className="text-center font-bold text-ink-soft">
          {t("premium.soon")}
        </p>
      )}
    </Card>
  );
}

export function Pricing() {
  const t = useT();
  return (
    <section id="pricing" className="bg-snow py-16">
      <div className="mx-auto max-w-4xl px-4">
        <h2 className="mb-2 text-center text-3xl">{t("landing.pricing.title")}</h2>
        <p className="mb-10 text-center text-ink-soft">{t("landing.pricing.subtitle")}</p>
        <div className="grid gap-6 md:grid-cols-2">
          <PlanCard id="free" count={4} />
          <PlanCard id="premium" featured count={4} />
        </div>
      </div>
    </section>
  );
}
