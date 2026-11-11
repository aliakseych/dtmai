"use client";
import { PrioritySlots } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { MAX_DREAMS, moveItem } from "@/lib/dreams";
import { LyceumName } from "./LyceumName";

/** Controlled 1-2-3 lyceum priority editor with the admission rules note. */
export function PriorityList({ ids, onChange, disabled, showRules = true }: { ids: string[]; onChange: (ids: string[]) => void; disabled?: boolean; showRules?: boolean }) {
  const t = useT();
  return (
    <section aria-label={t("dream.priority.title")} className="flex flex-col gap-3">
      <h3 className="text-lg font-extrabold text-ink">{t("dream.priority.title")}</h3>
      <PrioritySlots
        items={ids.map((id) => ({ id, label: <LyceumName id={id} /> }))}
        max={MAX_DREAMS}
        emptyText={t("dream.priority.empty")}
        disabled={disabled}
        labels={{ up: t("dream.priority.up"), down: t("dream.priority.down"), remove: t("dream.priority.remove"), slot: (n) => t("dream.priority.slot", { n }) }}
        onMove={(from, to) => onChange(moveItem(ids, from, to))}
        onRemove={(id) => onChange(ids.filter((x) => x !== id))}
      />
      {showRules && (
        <details className="rounded-2xl border-2 border-line bg-snow px-4 py-3 text-sm text-ink">
          <summary className="cursor-pointer font-extrabold text-brand">{t("dream.rules.title")}</summary>
          <p className="mt-2 break-words text-ink-soft">{t("dream.rules.body")}</p>
        </details>
      )}
    </section>
  );
}
