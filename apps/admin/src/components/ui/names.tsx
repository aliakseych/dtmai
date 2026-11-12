"use client";
import { useT } from "@/lib/i18n";
import { LOCALE_LIST, type Names } from "@/lib/util";
import { Input } from "./controls";

/** Editor for a `{locale: text}` map over the four platform locales. */
export function NamesEditor({ value, onChange, label, error }: { value: Names; onChange: (v: Names) => void; label?: string; error?: string }) {
  const t = useT();
  return (
    <fieldset className="rounded-xl border border-line p-2">
      <legend className="px-1 text-xs font-extrabold uppercase tracking-wide text-ink-soft">{label ?? t("admin.common.names")}</legend>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {LOCALE_LIST.map((l) => (
          <label key={l} className="flex items-center gap-1.5 text-xs">
            <span className="w-12 shrink-0 font-extrabold text-ink-soft">{l}</span>
            <Input value={value[l] ?? ""} onChange={(e) => onChange({ ...value, [l]: e.target.value })} />
          </label>
        ))}
      </div>
      {error && <span role="alert" className="mt-1 block text-xs font-bold text-red-deep">{error}</span>}
    </fieldset>
  );
}

/** Drops empty locales (API requires at least one non-empty). */
export const cleanNames = (n: Names): Names => Object.fromEntries(Object.entries(n).filter(([, v]) => v.trim()));
