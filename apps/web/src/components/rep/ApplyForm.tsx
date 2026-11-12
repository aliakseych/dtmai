"use client";
import { useState } from "react";
import { Button, Card } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { rep } from "./repApi";
import { repErrorKey } from "./repErrors";
import type { Membership } from "./repApi";

/** Proof-of-affiliation form for a lyceum without an approved membership. */
export function ApplyForm({ lyceumId, rejected, onApplied }: { lyceumId: string; rejected: boolean; onApplied: (m: Membership) => void }) {
  const t = useT();
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      onApplied(await rep.apply(lyceumId, note.trim()));
    } catch (e2) {
      setErr(t(repErrorKey(e2)));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card>
      <form onSubmit={submit} className="flex flex-col gap-3">
        <h2 className="text-xl text-ink">{t("rep.apply.title")}</h2>
        {rejected && <p className="text-sm font-bold text-red-deep">{t("rep.status.rejected")}</p>}
        <label className="flex flex-col gap-1">
          <span className="text-sm font-bold text-ink-soft">{t("rep.apply.proof")}</span>
          <textarea
            required
            rows={4}
            maxLength={1000}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder={t("rep.apply.proofHint")}
            className="rounded-2xl border-2 border-line bg-snow px-4 py-3 text-ink focus:border-brand focus:bg-white"
          />
        </label>
        {err && <p role="alert" className="text-sm font-bold text-red-deep">{err}</p>}
        <Button type="submit" disabled={busy || !note.trim()}>
          {t("rep.apply.submit")}
        </Button>
      </form>
    </Card>
  );
}
