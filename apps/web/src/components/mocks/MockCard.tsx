"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button, Card } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { api, type Mock } from "@/lib/api";
import { useLearnLanguage } from "@/lib/auth";
import { pick } from "@/lib/localized";

export function MockCard({ mock }: { mock: Mock }) {
  const t = useT();
  const router = useRouter();
  const { locale } = useLocale();
  const language = useLearnLanguage();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);

  async function start() {
    setBusy(true);
    setError(false);
    try {
      const a = await api.unwrap(api.client.POST("/v1/assessment/attempts", { body: { blueprint_id: mock.id, language } }));
      router.push(`/mocks/run/?attempt=${a.id}`);
    } catch {
      setBusy(false);
      setError(true);
    }
  }

  return (
    <Card className="flex cursor-pointer flex-col gap-2 hover:border-brand" onClick={() => !busy && void start()}>
      <div className="flex items-center justify-between gap-4">
        <div>
          <h3 className="text-lg">{pick(mock.names, locale) || mock.code}</h3>
          <p className="text-ink-soft">
            {t("mocks.questions", { n: mock.question_count })} · {t("mocks.minutes", { n: mock.duration_min })}
          </p>
        </div>
        <Button disabled={busy}>
          {busy ? t("mock.starting") : t("mocks.start")}
        </Button>
      </div>
      {error && (
        <p role="alert" className="font-bold text-red-deep">
          {t("mock.startError")}
        </p>
      )}
    </Card>
  );
}
