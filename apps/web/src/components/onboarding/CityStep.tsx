"use client";
import { useMemo, useState } from "react";
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
  const [sort, setSort] = useState<"name" | "count">("name");
  const items = useMemo(() => {
    const rows = cities.map((c) => ({ value: c.code, label: pick(c.names, locale), hint: String(c.lyceum_count), count: c.lyceum_count }));
    return rows.sort((a, b) => (sort === "count" ? b.count - a.count || a.label.localeCompare(b.label, locale) : a.label.localeCompare(b.label, locale)));
  }, [cities, locale, sort]);
  return (
    <>
    <div role="group" aria-label={t("onb.city.sort")} className="flex items-center gap-2 text-sm font-extrabold">
      <span className="text-ink-soft">{t("onb.city.sort")}</span>
      {(["name", "count"] as const).map((k) => (
        <button
          key={k}
          type="button"
          aria-pressed={sort === k}
          onClick={() => setSort(k)}
          className={sort === k ? "rounded-full bg-brand px-3 py-1 text-white" : "rounded-full border-2 border-line px-3 py-1 text-ink"}
        >
          {t(k === "name" ? "onb.city.sort.name" : "onb.city.sort.count")}
        </button>
      ))}
    </div>
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
    </>
  );
}
