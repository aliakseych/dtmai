"use client";
import { useT } from "@/lib/i18n";
import { Check } from "./controls";

export function MultiPick({ options, value, onChange, empty }: { options: { id: string; label: string }[]; value: string[]; onChange: (v: string[]) => void; empty?: string }) {
  const t = useT();
  if (options.length === 0) return <p className="text-xs text-ink-soft">{empty ?? t("admin.common.noOptions")}</p>;
  return (
    <div className="max-h-36 space-y-0.5 overflow-y-auto rounded-xl border border-line p-1.5">
      {options.map((o) => (
        <div key={o.id}>
          <Check checked={value.includes(o.id)} onChange={(c) => onChange(c ? [...value, o.id] : value.filter((x) => x !== o.id))} label={o.label} />
        </div>
      ))}
    </div>
  );
}
