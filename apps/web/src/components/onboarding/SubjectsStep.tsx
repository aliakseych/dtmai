"use client";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import type { Subject } from "@/lib/api";
import { pick } from "@/lib/localized";
import type { AsyncState } from "@/lib/useAsync";
import { Choice } from "./Choice";

export function SubjectsStep({ state, onRetry, value, onToggle, readOnly }: { state: AsyncState<Subject[]>; onRetry: () => void; value: string[]; onToggle: (id: string) => void; readOnly?: boolean }) {
  const t = useT();
  const { locale } = useLocale();
  return (
    <>
      <p className="text-ink-soft">{t(readOnly ? "onb.subjects.derived" : "onb.subjects.hint")}</p>
      <AsyncView state={state} onRetry={onRetry} isEmpty={(d) => d.length === 0}>
        {(d) => (
          <div role="group" aria-label={t("onb.title.subjects")} className="grid gap-2 sm:grid-cols-2">
            {d.filter((s) => !readOnly || value.includes(s.id)).map((s) =>
              readOnly ? (
                <div key={s.id} className="flex items-center gap-3 rounded-2xl border-2 border-line bg-snow px-4 py-3 font-extrabold text-ink">
                  {pick(s.names, locale)}
                </div>
              ) : (
              <Choice key={s.id} multi on={value.includes(s.id)} onClick={() => onToggle(s.id)}>
                {pick(s.names, locale)}
              </Choice>
              ),
            )}
          </div>
        )}
      </AsyncView>
    </>
  );
}
