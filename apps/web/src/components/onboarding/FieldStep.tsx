"use client";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { pick } from "@/lib/localized";
import type { Names } from "@/lib/api";
import type { FieldRow } from "@/lib/fields";
import type { AsyncState } from "@/lib/useAsync";
import { Choice } from "./Choice";

/** Fields of study (edu.uz specialities); each shows its subject pair. Chosen before the lyceum, so all are listed. */
export function FieldStep({ state, onRetry, subjectNames, value, onChange }: { state: AsyncState<FieldRow[]>; onRetry: () => void; subjectNames: Map<string, Names>; value: string | null; onChange: (code: string) => void }) {
  const t = useT();
  const { locale } = useLocale();
  return (
    <>
      <p className="text-ink-soft">{t("onb.field.hint")}</p>
      <AsyncView state={state} onRetry={onRetry}>
        {(all) => {
          const items = all;
          if (items.length === 0) return <p className="text-ink-soft">{t("onb.field.none")}</p>;
          return (
            <div role="radiogroup" aria-label={t("onb.title.field")} className="flex max-h-[50vh] flex-col gap-2 overflow-y-auto pr-1">
              {items.map((f) => (
                <Choice key={f.code} on={value === f.code} onClick={() => onChange(f.code)}>
                  {f.name}
                  {f.subject_ids.length > 0 && (
                    <span className="block text-sm font-bold text-ink-soft">
                      {f.subject_ids.map((id) => (subjectNames.has(id) ? pick(subjectNames.get(id)!, locale) : null)).filter(Boolean).join(" · ")}
                    </span>
                  )}
                </Choice>
              ))}
            </div>
          );
        }}
      </AsyncView>
    </>
  );
}
