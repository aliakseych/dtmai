"use client";
import { useT } from "@dtmai/i18n";
import { Choice } from "./Choice";

/** City options come from the lyceum list; with no city data the learner types it. */
export function CityStep({ cities, value, onChange }: { cities: string[]; value: string; onChange: (v: string) => void }) {
  const t = useT();
  if (cities.length === 0)
    return (
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={t("onb.city.placeholder")}
        aria-label={t("onb.city.placeholder")}
        autoComplete="address-level2"
        className="w-full rounded-2xl border-2 border-line bg-snow px-4 py-3 font-bold text-ink focus:border-blue focus:bg-white"
      />
    );
  return (
    <div role="radiogroup" aria-label={t("onb.city.q")} className="grid gap-2 sm:grid-cols-2">
      {cities.map((c) => (
        <Choice key={c} on={value === c} onClick={() => onChange(c)}>
          {c}
        </Choice>
      ))}
    </div>
  );
}
