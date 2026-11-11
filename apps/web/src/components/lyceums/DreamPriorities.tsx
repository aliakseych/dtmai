"use client";
import { useState } from "react";
import { useT } from "@dtmai/i18n";
import { dreamIds, saveDreams } from "@/lib/dreams";
import { useAuth } from "@/lib/auth";
import { PriorityList } from "./PriorityList";

/** Profile-bound priority editor: saves each change to /me and reloads it. */
export function DreamPriorities() {
  const t = useT();
  const { me, reloadMe } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  if (!me) return null;
  const change = async (ids: string[]) => {
    setBusy(true);
    setError(false);
    try {
      await saveDreams(ids);
      await reloadMe();
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="flex flex-col gap-2 rounded-card border-2 border-line bg-white p-4">
      <PriorityList ids={dreamIds(me)} onChange={change} disabled={busy} />
      {error && <p role="alert" className="text-sm font-bold text-red">{t("common.error")}</p>}
    </div>
  );
}
