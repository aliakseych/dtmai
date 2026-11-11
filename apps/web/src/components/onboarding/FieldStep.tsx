"use client";
import { useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import type { FieldRow } from "@/lib/fields";
import type { AsyncState } from "@/lib/useAsync";
import { Choice } from "./Choice";

/** Fields of study (edu.uz specialities) offered by the first-priority lyceum. */
export function FieldStep({ state, onRetry, offered, value, onChange }: { state: AsyncState<FieldRow[]>; onRetry: () => void; offered: string[]; value: string | null; onChange: (code: string) => void }) {
  const t = useT();
  return (
    <>
      <p className="text-ink-soft">{t("onb.field.hint")}</p>
      <AsyncView state={state} onRetry={onRetry}>
        {(all) => {
          const items = all.filter((f) => offered.includes(f.code));
          if (items.length === 0) return <p className="text-ink-soft">{t("onb.field.none")}</p>;
          return (
            <div role="radiogroup" aria-label={t("onb.title.field")} className="flex max-h-[50vh] flex-col gap-2 overflow-y-auto pr-1">
              {items.map((f) => (
                <Choice key={f.code} on={value === f.code} onClick={() => onChange(f.code)}>
                  {f.name}
                </Choice>
              ))}
            </div>
          );
        }}
      </AsyncView>
    </>
  );
}
