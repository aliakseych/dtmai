"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button, Card } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { api } from "@/lib/api";
import { useLearnLanguage } from "@/lib/auth";
import { useBilling } from "@/lib/billing";
import { isCode } from "@/lib/errors";
import { pick } from "@/lib/localized";
import { isActiveConflict, StartFailure } from "./StartFailure";
import { useSubjectNames } from "./useSubjectNames";

type Status = "idle" | "busy" | "premium" | "error" | "conflict";

/** Personal mock from weak areas; a 403 premium_required becomes a note (buy link only if canBuy). */
export function PersonalMockCard() {
  const t = useT();
  const router = useRouter();
  const { locale } = useLocale();
  const language = useLearnLanguage();
  const { canBuy } = useBilling();
  const { subjects } = useSubjectNames();
  const [subject, setSubject] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const chosen = subject || subjects[0]?.id || "";

  async function start() {
    setStatus("busy");
    try {
      const a = await api.unwrap(api.client.POST("/v1/assessment/attempts/personal", { body: { subject_id: chosen, language, count: 30 } }));
      router.push(`/mocks/run/?attempt=${a.id}`);
    } catch (e) {
      setStatus(isCode(e, "premium_required") ? "premium" : isActiveConflict(e) ? "conflict" : "error");
    }
  }

  return (
    <Card className="flex flex-col gap-3">
      <div>
        <h2 className="text-lg">{t("mock.personal")}</h2>
        <p className="text-ink-soft">{t("mock.personalHint")}</p>
      </div>
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-sm font-bold uppercase text-ink-soft">
          {t("mock.subject")}
          <select value={chosen} onChange={(e) => setSubject(e.target.value)} className="rounded-2xl border-2 border-line bg-snow px-3 py-3 text-base normal-case text-ink">
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {pick(s.names, locale)}
              </option>
            ))}
          </select>
        </label>
        <Button onClick={start} disabled={!chosen || status === "busy"}>
          {status === "busy" ? t("mock.starting") : t("mock.personalStart")}
        </Button>
      </div>
      {status === "premium" && (
        <p role="status" className="font-bold text-ink">
          {t("mock.premiumNote")}{" "}
          {canBuy && (
            <Link href="/premium/" className="text-brand underline">
              {t("mock.premiumGo")}
            </Link>
          )}
        </p>
      )}
      {(status === "error" || status === "conflict") && <StartFailure conflict={status === "conflict"} />}
    </Card>
  );
}
