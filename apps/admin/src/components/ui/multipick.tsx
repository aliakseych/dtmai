"use client";
import { Check } from "./controls";

export function MultiPick({ options, value, onChange, empty = "No options" }: { options: { id: string; label: string }[]; value: string[]; onChange: (v: string[]) => void; empty?: string }) {
  if (options.length === 0) return <p className="text-xs text-ink-soft">{empty}</p>;
  return (
    <div className="max-h-36 space-y-0.5 overflow-y-auto rounded-md border border-line p-1.5">
      {options.map((o) => (
        <div key={o.id}>
          <Check checked={value.includes(o.id)} onChange={(c) => onChange(c ? [...value, o.id] : value.filter((x) => x !== o.id))} label={o.label} />
        </div>
      ))}
    </div>
  );
}
