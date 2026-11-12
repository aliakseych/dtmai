"use client";
import { useMemo, useState } from "react";
import { useLocale, useT } from "@dtmai/i18n";
import { ChoiceDropdown, cn } from "@dtmai/ui";
import { AsyncView } from "@/components/AsyncView";
import { PageTitle } from "@/components/PageTitle";
import { DreamPriorities } from "@/components/lyceums/DreamPriorities";
import { LyceumCard } from "@/components/lyceums/LyceumCard";
import { api } from "@/lib/api";
import { fetchCities } from "@/lib/cities";
import { pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";

export function LyceumsView() {
  const t = useT();
  const { locale } = useLocale();
  const [q, setQ] = useState("");
  const [city, setCity] = useState("");
  const [open, setOpen] = useState<string | null>(null);
  const { state, reload } = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums", { params: { query: { q: q || undefined } } })), [q]);
  const cityState = useAsync(fetchCities, []);
  const cities = useMemo(() => {
    const all = cityState.state.status === "ready" ? cityState.state.data : [];
    return all.map((c) => ({ code: c.code, name: pick(c.names, locale), count: c.lyceum_count })).sort((a, b) => a.name.localeCompare(b.name, locale));
  }, [cityState.state, locale]);
  const cityName = (code?: string | null) => cities.find((c) => c.code === code)?.name;
  return (
    <>
      <PageTitle>{t("lyceums.title")}</PageTitle>
      <div className="mb-4"><DreamPriorities /></div>
      <div className="mb-4 flex flex-col gap-2 sm:flex-row">
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t("lyceums.search")}
          aria-label={t("lyceums.search")}
          className="w-full rounded-2xl border-2 border-line bg-snow px-4 py-3 text-ink focus:border-brand focus:bg-white"
        />
        <ChoiceDropdown
          className="sm:w-56"
          label={t("lyceums.city")}
          value={city}
          onChange={setCity}
          pinned={[{ value: "", label: t("lyceums.city.all") }]}
          items={cities.filter((c) => c.count > 0).map((c) => ({ value: c.code, label: c.name, hint: String(c.count) }))}
          searchPlaceholder={t("onb.city.search")}
          emptyText={t("onb.city.none")}
        />
      </div>
      <AsyncView state={state} onRetry={reload} isEmpty={(d) => d.length === 0} emptyText={t("lyceums.none")}>
        {(all) => {
          const list = city ? all.filter((l) => l.city === city) : all;
          if (list.length === 0) return <p className="py-10 text-center text-ink-soft">{t("lyceums.none")}</p>;
          return (
            <div className="grid max-h-[75vh] gap-3 overflow-y-auto pr-1 md:grid-cols-2">
              {list.map((l) => (
                <div key={l.id} className={cn("min-w-0", open === l.id && "md:col-span-2")}>
                  <LyceumCard summary={l} title={pick(l.names, locale)} cityName={cityName(l.city)} open={open === l.id} onToggle={() => setOpen(open === l.id ? null : l.id)} />
                </div>
              ))}
            </div>
          );
        }}
      </AsyncView>
    </>
  );
}
