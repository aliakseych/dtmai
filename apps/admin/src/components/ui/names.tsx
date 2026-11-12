"use client";
import { useEffect, useRef, useState } from "react";
import { useT } from "@/lib/i18n";
import { LOCALE_LIST, type Names } from "@/lib/util";
import { Input } from "./controls";

/** Editor for a `{locale: text}` map over the four platform locales. */
export function NamesEditor({ value, onChange, label, error }: { value: Names; onChange: (v: Names) => void; label?: string; error?: string }) {
  const t = useT();
  const ref = useRef<HTMLFieldSetElement>(null);
  const [dismissed, setDismissed] = useState<string | undefined>();
  const shown = error && error !== dismissed ? error : undefined;
  useEffect(() => {
    const ctl = ref.current?.querySelector<HTMLElement>("input");
    if (!ctl) return;
    ref.current?.querySelectorAll("input").forEach((i) => (shown ? i.setAttribute("aria-invalid", "true") : i.removeAttribute("aria-invalid")));
    if (!shown) return;
    const root = ref.current?.closest("[role=dialog],dialog,form") ?? document;
    if (root.querySelector("[aria-invalid=true]") === ctl) ctl.focus();
    const clear = () => setDismissed(error);
    ref.current?.addEventListener("input", clear, { once: true });
    const el = ref.current;
    return () => el?.removeEventListener("input", clear);
  }, [shown, error]);
  return (
    <fieldset ref={ref} className="rounded-xl border border-line p-2">
      <legend className="px-1 text-xs font-extrabold uppercase tracking-wide text-ink-soft">{label ?? t("admin.common.names")}</legend>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {LOCALE_LIST.map((l) => (
          <label key={l} className="flex items-center gap-1.5 text-xs">
            <span className="w-12 shrink-0 font-extrabold text-ink-soft">{l}</span>
            <Input value={value[l] ?? ""} onChange={(e) => onChange({ ...value, [l]: e.target.value })} />
          </label>
        ))}
      </div>
      {shown && <span role="alert" className="mt-1 block text-xs font-bold text-red-deep">{shown}</span>}
    </fieldset>
  );
}

/** Drops empty locales (API requires at least one non-empty). */
export const cleanNames = (n: Names): Names => Object.fromEntries(Object.entries(n).filter(([, v]) => v.trim()));
