"use client";
import { useMemo } from "react";
import { useLocale, useT } from "@dtmai/i18n";
import { ChoiceList } from "@dtmai/ui";
import { AsyncView } from "@/components/AsyncView";
import type { City } from "@/lib/cities";
import { pick } from "@/lib/localized";
import type { AsyncState } from "@/lib/useAsync";

const ANY = "__any__";

/** `undefined` = not chosen yet, `null` = "any city", string = city code. */
export type CityChoice = string | null | undefined;

export function CityStep({ state, onRetry, value, onChange }: { state: AsyncState<City[]>; onRetry: () => void; value: CityChoice; onChange: (v: string | null) => void }) {
  const t = useT();
  const { locale } = useLocale();
  return (
    <>
      <p className="text-ink-soft">{t("onb.city.hint")}</p>
      <AsyncView state={state} onRetry={onRetry}>
        {(cities) => <List cities={cities} locale={locale} value={value} onChange={onChange} />}
      </AsyncView>
    </>
  );
}

function List({ cities, locale, value, onChange }: { cities: City[]; locale: Parameters<typeof pick>[1]; value: CityChoice; onChange: (v: string | null) => void }) {
  const t = useT();
  const items = useMemo(
    () => cities.map((c) => ({ value: c.code, label: pick(c.names, locale), hint: String(c.lyceum_count) })).sort((a, b) => a.label.localeCompare(b.label, locale)),
    [cities, locale],
  );
  return (
    <ChoiceList
      label={t("onb.city.q")}
      items={items}
      pinned={[{ value: ANY, label: t("onb.city.any") }]}
      value={value === undefined ? null : value === null ? ANY : value}
      onChange={(v) => onChange(v === ANY ? null : v)}
      searchPlaceholder={t("onb.city.search")}
      emptyText={t("onb.city.none")}
      columns
    />
  );
}
