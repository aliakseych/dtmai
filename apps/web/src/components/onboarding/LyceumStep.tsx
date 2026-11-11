"use client";
import { useMemo, useState } from "react";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { pick } from "@/lib/localized";
import type { AsyncState } from "@/lib/useAsync";
import { Choice } from "./Choice";
import { normCity, type OnbLyceum } from "./types";

/** Lyceums of the chosen city (all of them when the city matches none), with logo/campus photo when the API has them. */
export function LyceumStep({ state, onRetry, city, value, onChange }: { state: AsyncState<OnbLyceum[]>; onRetry: () => void; city: string; value: string | null; onChange: (id: string) => void }) {
  const t = useT();
  const { locale } = useLocale();
  const [q, setQ] = useState("");
  return (
    <>
      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder={t("lyceums.search")}
        aria-label={t("lyceums.search")}
        className="w-full rounded-2xl border-2 border-line bg-snow px-4 py-3 text-ink focus:border-blue focus:bg-white"
      />
      <AsyncView state={state} onRetry={onRetry} isEmpty={(d) => d.length === 0}>
        {(d) => <List all={d} city={city} q={q} value={value} onChange={onChange} locale={locale} />}
      </AsyncView>
    </>
  );
}

function List({ all, city, q, value, onChange, locale }: { all: OnbLyceum[]; city: string; q: string; value: string | null; onChange: (id: string) => void; locale: Parameters<typeof pick>[1] }) {
  const items = useMemo(() => {
    const c = normCity(city);
    const inCity = c ? all.filter((l) => l.city && normCity(l.city) === c) : [];
    const base = inCity.length > 0 ? inCity : all;
    const needle = q.trim().toLowerCase();
    return needle ? base.filter((l) => pick(l.names, locale).toLowerCase().includes(needle)) : base;
  }, [all, city, q, locale]);
  return (
    <div role="radiogroup" className="flex flex-col gap-2">
      {items.map((l) => (
        <Choice key={l.id} on={value === l.id} onClick={() => onChange(l.id)}>
          {l.logo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={l.logo_url} alt="" className="size-10 shrink-0 rounded-lg object-contain" />
          ) : null}
          <span className="flex-1">{pick(l.names, locale)}</span>
          {l.campus_photo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={l.campus_photo_url} alt="" loading="lazy" className="h-12 w-20 shrink-0 rounded-lg object-cover" />
          ) : null}
        </Choice>
      ))}
    </div>
  );
}
