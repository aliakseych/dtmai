"use client";
import { Card } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { fmt } from "@/lib/localized";
import type { PredictionView } from "@/lib/api";

export function PredictionCard({ view }: { view: PredictionView }) {
  const t = useT();
  const { locale } = useLocale();
  const num = fmt(locale);
  const p = view.prediction;
  if (!p) return null;
  return (
    <Card className="flex flex-col gap-1">
      <p className="text-sm font-bold uppercase text-ink-soft">{t("mock.prediction")}</p>
      <p className="text-4xl font-extrabold text-brand">{num.format(p.value)}</p>
      <p className="font-bold text-ink-soft">{t("mock.predictionBand", { low: num.format(p.low), high: num.format(p.high) })}</p>
      {!p.confident && <p className="text-sm text-ink-soft">{t("mock.predictionRough")}</p>}
    </Card>
  );
}
