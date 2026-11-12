"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { ApiError } from "@dtmai/api-client";
import { motion, useReducedMotion } from "motion/react";
import { Button, buttonClass, Card, Icon, Mascot, type IconName } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { api, type FinishOut, type SessionOut } from "@/lib/api";
import { useAuth, useLearnLanguage } from "@/lib/auth";
import { pick } from "@/lib/localized";
import { refreshStats } from "@/lib/stats";
import { useAsync } from "@/lib/useAsync";
import { RushRunner } from "./RushRunner";

/** Decorative only: tiles cycle through these; subjects themselves come from the API. */
const SUBJECT_ICONS: IconName[] = ["learn", "bolt", "review", "mocks", "leagues", "lyceums"];

type Phase = { name: "pick" } | { name: "run"; session: SessionOut } | { name: "done"; result: FinishOut };

export function RushView() {
  const t = useT();
  const reduce = useReducedMotion();
  const { locale } = useLocale();
  const language = useLearnLanguage();
  const { me } = useAuth();
  const preset = useSearchParams().get("subject");
  const subjects = useAsync(() => api.unwrap(api.client.GET("/v1/catalog/subjects")), []);
  const [subject, setSubject] = useState<string | null>(preset);
  const [phase, setPhase] = useState<Phase>({ name: "pick" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = async (subject_id: string) => {
    setBusy(true);
    setError(null);
    try {
      setPhase({ name: "run", session: await api.unwrap(api.client.POST("/v1/learning/rush/start", { body: { subject_id, language } })) });
    } catch (e) {
      const code = e instanceof ApiError ? e.code : undefined;
      setError(code === "no_questions" ? t("err.noQuestions") : e instanceof ApiError && e.status === 409 ? t("err.conflict") : t("common.error"));
    } finally {
      setBusy(false);
    }
  };

  if (phase.name === "run")
    return (
      <RushRunner
        session={phase.session}
        onDone={(result) => {
          setPhase({ name: "done", result });
          void refreshStats().catch(() => undefined);
        }}
      />
    );

  if (phase.name === "done") {
    const r = phase.result;
    return (
      <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-5 p-6 text-center">
        <Mascot mood="celebrate" size={160} alt="" />
        <h1 className="text-3xl">{t("rush.done")}</h1>
        <div className="grid w-full grid-cols-2 gap-3">
          <Card className="flex flex-col items-center">
            <span className="text-3xl font-extrabold text-ink">{r.points ?? 0}</span>
            <span className="text-ink-soft">{t("rush.points")}</span>
          </Card>
          <Card className="flex flex-col items-center">
            <span className="text-3xl font-extrabold text-ink">+{r.xp_base}</span>
            <span className="text-ink-soft">{t("stat.xp")}</span>
          </Card>
          <Card className="flex flex-col items-center">
            <span className="text-3xl font-extrabold text-ink">
              {r.correct}/{r.answered}
            </span>
            <span className="text-ink-soft">{t("rush.correct")}</span>
          </Card>
          <Card className="flex flex-col items-center">
            <span className="text-3xl font-extrabold text-ink">{r.best_streak ?? 0}</span>
            <span className="text-ink-soft">{t("rush.bestStreak")}</span>
          </Card>
        </div>
        <Button className="w-full" onClick={() => setPhase({ name: "pick" })}>
          {t("rush.again")}
        </Button>
        <Link href="/practice/" className={buttonClass("secondary", true)}>
          {t("rush.back")}
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-5 p-6 text-center">
      <Mascot mood="rush" size={140} alt="" />
      <h1 className="text-3xl">{t("rush.title")}</h1>
      <p className="text-ink-soft">{t("rush.rules")}</p>
      <AsyncView state={subjects.state} onRetry={subjects.reload} isEmpty={(d) => d.length === 0}>
        {(list) => {
          const mine = me?.subject_ids ?? [];
          const sorted = [...list].sort((a, b) => Number(!mine.includes(a.id)) - Number(!mine.includes(b.id)));
          const current = subject ?? sorted[0].id;
          return (
            <div className="flex w-full flex-col gap-3">
              <div className="grid w-full grid-cols-2 gap-3" role="radiogroup" aria-label={t("rush.subject")}>
                {sorted.map((s, i) => {
                  const on = s.id === current;
                  return (
                    <motion.button
                      key={s.id}
                      type="button"
                      role="radio"
                      aria-checked={on}
                      onClick={() => setSubject(s.id)}
                      animate={{ scale: on && !reduce ? 1.04 : 1 }}
                      whileTap={reduce ? undefined : { scale: 0.96 }}
                      transition={{ type: "spring", stiffness: 400, damping: 18 }}
                      className={`flex min-w-0 flex-col items-center gap-2 rounded-2xl border-2 border-b-4 p-3 font-extrabold ${on ? "border-brand bg-brand-soft text-ink" : "border-line bg-white text-ink"}`}
                    >
                      <span className={`grid size-14 place-items-center rounded-2xl ${on ? "bg-accent" : "bg-brand-soft"}`}>
                        <Icon name={SUBJECT_ICONS[i % SUBJECT_ICONS.length]} size={28} className={on ? "text-ink" : "text-brand"} />
                      </span>
                      <span className="w-full min-w-0 break-words">{pick(s.names, locale)}</span>
                    </motion.button>
                  );
                })}
              </div>
              {error && (
                <p role="alert" className="font-bold text-red-deep">
                  {error}
                </p>
              )}
              <Button disabled={busy} onClick={() => void start(current)}>
                {t("rush.start")}
              </Button>
            </div>
          );
        }}
      </AsyncView>
      <Link href="/practice/" className={buttonClass("secondary", true)}>
        {t("rush.back")}
      </Link>
    </main>
  );
}
