"use client";
import { useState } from "react";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { PageTitle } from "@/components/PageTitle";
import { LyceumCard } from "@/components/lyceums/LyceumCard";
import { useLyceumDetails } from "@/components/lyceums/useLyceumDetail";
import { api } from "@/lib/api";
import { pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";

export function LyceumsView() {
  const t = useT();
  const { locale } = useLocale();
  const [q, setQ] = useState("");
  const [city, setCity] = useState("");
  const [open, setOpen] = useState<string | null>(null);
  const { state, reload } = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums", { params: { query: { q: q || undefined } } })), [q]);
  const details = useLyceumDetails(state.status === "ready" ? state.data.map((l) => l.id) : []);
  // The list summary has no city, so options come from the loaded lyceum profiles.
  const cities = Array.from(new Set(Object.values(details).map((d) => d.profile.city).filter((c): c is string => !!c))).sort((a, b) => a.localeCompare(b));
  return (
    <>
      <PageTitle>{t("lyceums.title")}</PageTitle>
      <div className="mb-4 flex flex-col gap-2 sm:flex-row">
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t("lyceums.search")}
          aria-label={t("lyceums.search")}
          className="w-full rounded-2xl border-2 border-line bg-snow px-4 py-3 text-ink focus:border-blue focus:bg-white"
        />
        <select
          value={city}
          onChange={(e) => setCity(e.target.value)}
          aria-label={t("lyceums.city")}
          className="rounded-2xl border-2 border-line bg-snow px-4 py-3 text-ink focus:border-blue focus:bg-white sm:w-56"
        >
          <option value="">{t("lyceums.city.all")}</option>
          {cities.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>
      <AsyncView state={state} onRetry={reload} isEmpty={(d) => d.length === 0} emptyText={t("lyceums.none")}>
        {(all) => {
          const list = city ? all.filter((l) => details[l.id]?.profile.city === city) : all;
          if (list.length === 0) return <p className="py-10 text-center text-ink-soft">{t("lyceums.none")}</p>;
          return (
            <div className="grid gap-3 lg:grid-cols-2">
              {list.map((l) => (
                <div key={l.id} className={open === l.id ? "lg:col-span-2" : undefined}>
                  <LyceumCard
                    summary={l}
                    detail={details[l.id]}
                    title={pick(l.names, locale)}
                    open={open === l.id}
                    onToggle={() => setOpen(open === l.id ? null : l.id)}
                  />
                </div>
              ))}
            </div>
          );
        }}
      </AsyncView>
    </>
  );
}
