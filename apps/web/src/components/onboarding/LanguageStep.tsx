"use client";
import { useLocale } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import type { Language } from "@/lib/api";
import { pick } from "@/lib/localized";
import type { AsyncState } from "@/lib/useAsync";
import { Choice } from "./Choice";

export function LanguageStep({ state, onRetry, value, onChange }: { state: AsyncState<Language[]>; onRetry: () => void; value: string | null; onChange: (id: string) => void }) {
  const { locale } = useLocale();
  return (
    <AsyncView state={state} onRetry={onRetry} isEmpty={(d) => d.length === 0}>
      {(d) => (
        <div role="radiogroup" className="grid gap-2">
          {d.filter((l) => l.code === "uz" || l.code === "ru").map((l) => (
            <Choice key={l.id} on={value === l.id} onClick={() => onChange(l.id)}>
              {pick(l.names, locale)}
            </Choice>
          ))}
        </div>
      )}
    </AsyncView>
  );
}
