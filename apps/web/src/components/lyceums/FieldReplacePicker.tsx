"use client";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { api } from "@/lib/api";
import { pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";

/** Lyceums offering `fieldCode` (minus `exclude`); picking one replaces a mismatching priority. */
export function FieldReplacePicker({ fieldCode, exclude, onPick, onCancel }: { fieldCode: string; exclude: string[]; onPick: (id: string) => void; onCancel: () => void }) {
  const t = useT();
  const { locale } = useLocale();
  const { state, reload } = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums", { params: { query: { limit: 200 } } })), []);
  return (
    <section aria-label={t("field.replace.title")} className="flex flex-col gap-2 rounded-2xl border-2 border-line bg-snow p-3">
      <div className="flex items-center justify-between gap-2">
        <h4 className="font-extrabold text-ink">{t("field.replace.title")}</h4>
        <button type="button" onClick={onCancel} className="text-sm font-extrabold text-brand">
          {t("field.replace.cancel")}
        </button>
      </div>
      <AsyncView state={state} onRetry={reload}>
        {(rows) => {
          const items = rows.filter((l) => l.field_codes.includes(fieldCode) && !exclude.includes(l.id));
          if (items.length === 0) return <p className="text-sm text-ink-soft">{t("field.replace.none")}</p>;
          return (
            <div className="flex max-h-48 flex-col gap-1 overflow-y-auto">
              {items.map((l) => (
                <button key={l.id} type="button" onClick={() => onPick(l.id)} className="rounded-xl border-2 border-line bg-white px-3 py-2 text-left font-bold text-ink hover:bg-snow">
                  {pick(l.names, locale)}
                </button>
              ))}
            </div>
          );
        }}
      </AsyncView>
    </section>
  );
}
