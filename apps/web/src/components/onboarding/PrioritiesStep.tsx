"use client";
import { useState } from "react";
import { useT } from "@dtmai/i18n";
import { FieldReplacePicker } from "@/components/lyceums/FieldReplacePicker";
import { PriorityList } from "@/components/lyceums/PriorityList";
import type { LyceumRow } from "@/lib/api";
import { mismatchIds } from "@/lib/fields";
import type { AsyncState } from "@/lib/useAsync";
import { LyceumStep } from "./LyceumStep";

/** Remaining priorities; lyceums lacking the chosen field get Replace / Remove. */
export function PrioritiesStep({ state, onRetry, city, value, onChange, fieldCode }: { state: AsyncState<LyceumRow[]>; onRetry: () => void; city: string | null; value: string[]; onChange: (ids: string[]) => void; fieldCode: string | null }) {
  const t = useT();
  const [replacing, setReplacing] = useState<string | null>(null);
  const rows = state.status === "ready" ? state.data : [];
  return (
    <>
      <p className="text-ink-soft">{t("onb.priorities.hint")}</p>
      <PriorityList ids={value} onChange={onChange} mismatch={mismatchIds(value, rows, fieldCode)} onReplace={fieldCode ? setReplacing : undefined} />
      {replacing && fieldCode && (
        <FieldReplacePicker
          fieldCode={fieldCode}
          exclude={value}
          onCancel={() => setReplacing(null)}
          onPick={(id) => {
            onChange(value.map((x) => (x === replacing ? id : x)));
            setReplacing(null);
          }}
        />
      )}
      <LyceumStep hideList state={state} onRetry={onRetry} city={city} value={value} onChange={onChange} />
    </>
  );
}
