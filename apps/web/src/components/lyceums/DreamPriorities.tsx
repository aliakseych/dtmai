"use client";
import { useState } from "react";
import { useT } from "@dtmai/i18n";
import { dreamIds, saveDreams } from "@/lib/dreams";
import { fetchFields } from "@/lib/fields";
import { useAuth } from "@/lib/auth";
import { useAsync } from "@/lib/useAsync";
import { FieldReplacePicker } from "./FieldReplacePicker";
import { PriorityList } from "./PriorityList";

/** Profile-bound priority editor: saves each change to /me and reloads it. Shows the chosen field and mismatches. */
export function DreamPriorities() {
  const t = useT();
  const { me, reloadMe } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const [replacing, setReplacing] = useState<string | null>(null);
  const fields = useAsync(fetchFields, []);
  if (!me) return null;
  const ids = dreamIds(me);
  const fieldName = me.field_code && fields.state.status === "ready" ? fields.state.data.find((f) => f.code === me.field_code)?.name : undefined;
  const change = async (next: string[]) => {
    setBusy(true);
    setError(false);
    try {
      await saveDreams(next);
      await reloadMe();
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="flex flex-col gap-2 rounded-card border-2 border-line bg-white p-4">
      {me.field_code && (
        <p className="text-sm font-extrabold text-ink">
          {t("field.current", { name: fieldName ?? me.field_code })}
        </p>
      )}
      <PriorityList ids={ids} onChange={change} disabled={busy} mismatch={me.dream_field_mismatch} onReplace={me.field_code ? setReplacing : undefined} />
      {replacing && me.field_code && (
        <FieldReplacePicker
          fieldCode={me.field_code}
          exclude={ids}
          onCancel={() => setReplacing(null)}
          onPick={(id) => {
            const from = replacing;
            setReplacing(null);
            void change(ids.map((x) => (x === from ? id : x)));
          }}
        />
      )}
      {error && <p role="alert" className="text-sm font-bold text-red">{t("common.error")}</p>}
    </div>
  );
}
