"use client";
import { useState } from "react";
import { Button, Card, cn, Mascot, useToast } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { PageTitle } from "@/components/PageTitle";
import { api } from "@/lib/api";
import { useBilling } from "@/lib/billing";
import { fmt, pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";

export function PremiumView() {
  const t = useT();
  const { locale } = useLocale();
  const toast = useToast();
  const { canBuy, premium } = useBilling();
  const plans = useAsync(() => api.unwrap(api.client.GET("/v1/billing/plans")), []);
  const [selected, setSelected] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function pay(plan_code: string) {
    setBusy(true);
    try {
      window.location.href = (await api.unwrap(api.client.POST("/v1/billing/checkout", { body: { plan_code } }))).pay_url;
    } catch {
      toast(t("common.error"), "error");
      setBusy(false);
    }
  }

  return (
    <>
      <div className="mb-6 flex flex-col items-center text-center">
        <Mascot mood="premium" size={180} alt={t("mascot.alt")} className="h-auto w-40" />
        <PageTitle>{t("premium.title")}</PageTitle>
        <p className="-mt-4 text-ink-soft">{t("premium.subtitle")}</p>
      </div>
      {premium && <p className="mb-4 text-center font-bold text-brand">{t("premium.active")}</p>}
      <AsyncView state={plans.state} onRetry={plans.reload} isEmpty={(d) => d.filter((p) => p.code !== "free").length === 0}>
        {(all) => {
          const list = all.filter((p) => p.code !== "free" && p.active);
          const current = selected ?? list[0]?.code;
          return (
            <div className="flex flex-col gap-3">
              {list.map((p) => (
                <button key={p.code} type="button" aria-pressed={current === p.code} onClick={() => setSelected(p.code)} className="text-left">
                  <Card className={cn("flex items-center justify-between gap-3", current === p.code && "border-brand bg-brand-soft")}>
                    <span className="text-lg text-ink">
                      {pick(p.names, locale)} <span className="text-sm text-ink-soft">· {t("plan.months", { n: p.period_months })}</span>
                    </span>
                    <span className="text-xl text-ink">
                      {fmt(locale).format(p.price_uzs)} {t("common.uzs")}
                    </span>
                  </Card>
                </button>
              ))}
              {canBuy ? (
                <Button variant="super" block disabled={busy || !current} onClick={() => current && void pay(current)}>
                  {t("premium.pay")}
                </Button>
              ) : (
                !premium && (
                  <p role="status" className="rounded-card border-2 border-line bg-snow p-4 text-center font-bold text-ink-soft">
                    {t("premium.soon")}
                  </p>
                )
              )}
            </div>
          );
        }}
      </AsyncView>
    </>
  );
}
