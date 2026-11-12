"use client";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Mascot } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { useDocumentTitle } from "@/components/PageTitle";
import { api } from "@/lib/api";
import { homeFor, useAuth } from "@/lib/auth";
import { routeForStartParam, setupTma, tmaStartParam } from "@/lib/tma";

type Phase = "opening" | "outside" | "failed";

export default function TelegramEntryPage() {
  const t = useT();
  useDocumentTitle(t("tg.title"));
  const router = useRouter();
  const { acceptTokens } = useAuth();
  const [phase, setPhase] = useState<Phase>("opening");
  const [attempt, setAttempt] = useState(0);

  const run = useCallback(async () => {
    setPhase("opening");
    try {
      const initData = await setupTma();
      if (!initData) return setPhase("outside");
      const tokens = await api.unwrap(api.client.POST("/v1/identity/telegram/webapp", { body: { init_data: initData } }));
      const me = await acceptTokens(tokens);
      const deepLink = routeForStartParam(await tmaStartParam());
      router.replace(deepLink && homeFor(me) !== "/onboarding/" ? deepLink : homeFor(me));
    } catch {
      setPhase("failed");
    }
  }, [acceptTokens, router]);

  useEffect(() => {
    void run();
  }, [run, attempt]);

  return (
    <div className="grid min-h-dvh place-items-center px-4 text-center">
      <div className="flex flex-col items-center gap-3">
        <Mascot mood={phase === "opening" ? "wave" : phase === "failed" ? "sad" : "thinking"} size={160} alt={t("mascot.alt")} className="h-auto w-36" />
        <h1 className="text-2xl">{t("tg.title")}</h1>
        <p role={phase === "failed" ? "alert" : "status"} className="text-ink-soft">
          {phase === "opening" ? t("tg.opening") : phase === "outside" ? t("tg.outside") : t("tg.failed")}
        </p>
        {phase === "failed" && <Button onClick={() => setAttempt((n) => n + 1)}>{t("common.retry")}</Button>}
      </div>
    </div>
  );
}
