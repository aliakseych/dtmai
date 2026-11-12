"use client";
import { useMemo, useState } from "react";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import type { LyceumRow } from "@/lib/api";
import { pick } from "@/lib/localized";
import type { AsyncState } from "@/lib/useAsync";
import { PriorityList } from "@/components/lyceums/PriorityList";
import { MAX_DREAMS } from "@/lib/dreams";
import { Choice } from "./Choice";

/** Lyceums of the chosen city code (all when "any city"), with logo/campus photo. */
export function LyceumStep({
  state,
  onRetry,
  city,
  value,
  onChange,
  single,
  hideList,
}: {
  state: AsyncState<LyceumRow[]>;
  onRetry: () => void;
  city: string | null;
  value: string[];
  onChange: (ids: string[]) => void;
  /** First-priority pick: exactly one lyceum, no priority list. */
  single?: boolean;
  /** The priorities step renders its own list above. */
  hideList?: boolean;
}) {
  const t = useT();
  const { locale } = useLocale();
  const [q, setQ] = useState("");
  return (
    <>
      {!single && !hideList && <PriorityList ids={value} onChange={onChange} />}
      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder={t("lyceums.search")}
        aria-label={t("lyceums.search")}
        className="w-full rounded-2xl border-2 border-line bg-snow px-4 py-3 text-ink focus:border-brand focus:bg-white"
      />
      <AsyncView state={state} onRetry={onRetry} isEmpty={(d) => d.length === 0}>
        {(d) => <List all={d} city={city} q={q} value={value} onChange={onChange} locale={locale} single={single} />}
      </AsyncView>
    </>
  );
}

function List({ all, city, q, value, onChange, locale, single }: { all: LyceumRow[]; city: string | null; q: string; value: string[]; onChange: (ids: string[]) => void; locale: Parameters<typeof pick>[1]; single?: boolean }) {
  const t = useT();
  // A city without lyceums must not dead-end the step: fall back to every lyceum.
  const inCity = city ? all.filter((l) => l.city === city) : all;
  const fallback = inCity.length === 0;
  const items = useMemo(() => {
    const base = fallback ? all : inCity;
    const needle = q.trim().toLowerCase();
    return needle ? base.filter((l) => pick(l.names, locale).toLowerCase().includes(needle)) : base;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [all, city, q, locale, fallback]);
  return (
    <>
      {fallback && <p className="rounded-xl bg-snow px-3 py-2 text-sm font-bold text-ink-soft">{t("onb.lyceum.noneInCity")}</p>}
    <div role="group" className="flex max-h-[45vh] flex-col gap-2 overflow-y-auto pr-1">
      {items.map((l) => (
        <Choice key={l.id} multi={!single} on={value.includes(l.id)} onClick={() => (single ? onChange([l.id]) : onChange(value.includes(l.id) ? value.filter((x) => x !== l.id) : value.length < MAX_DREAMS ? [...value, l.id] : value))}>
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
    </>
  );
}
