"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button, Card, cn, Mascot, ProgressBar } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { LessonPlayer } from "@/components/lesson/LessonPlayer";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";

const TOTAL = 3;

function Choice({ on, onClick, children }: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      aria-pressed={on}
      onClick={onClick}
      className={cn("rounded-2xl border-2 border-b-4 px-4 py-3 text-left font-extrabold", on ? "border-blue bg-blue-soft text-blue-deep" : "border-line bg-white")}
    >
      {children}
    </button>
  );
}

/** Target lyceum + education language, then an optional placement test. */
export function Onboarding() {
  const t = useT();
  const { locale } = useLocale();
  const router = useRouter();
  const { isGuest, reloadMe } = useAuth();
  const [step, setStep] = useState(1);
  const [lyceumId, setLyceumId] = useState<string | null>(null);
  const [languageId, setLanguageId] = useState<string | null>(null);
  const [subjectId, setSubjectId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [saveError, setSaveError] = useState(false);
  const [q, setQ] = useState("");

  const lyceums = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums", { params: { query: { limit: 200 } } })), []);
  const languages = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums/languages")), []);
  const subjects = useAsync(() => api.unwrap(api.client.GET("/v1/catalog/subjects")), []);

  const langCode = () => {
    const c = languages.state.status === "ready" ? languages.state.data.find((l) => l.id === languageId)?.code : undefined;
    return c === "ru" || c === "en" ? c : "uz";
  };

  async function save(): Promise<boolean> {
    if (!lyceumId || !languageId) return false;
    setBusy(true);
    setSaveError(false);
    try {
      await api.unwrap(api.client.PATCH("/v1/identity/me", { body: { target_lyceum_id: lyceumId, education_language_id: languageId } }));
      await reloadMe();
      return true;
    } catch {
      setSaveError(true);
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function startTest() {
    if (await save()) setStep(3);
  }

  /** Placement is optional: skipping records it so the path starts at unit 0. */
  async function skip() {
    if (!(await save())) return;
    try {
      if (subjectId) await api.unwrap(api.client.POST("/v1/learning/placement/{subject_id}/skip", { params: { path: { subject_id: subjectId } } }));
    } catch {
      /* skipping is best-effort; the path is reachable regardless */
    }
    router.replace("/learn/");
  }

  if (step === 3 && subjectId)
    return (
      <LessonPlayer
        load={() => api.unwrap(api.client.POST("/v1/learning/placement/start", { body: { subject_id: subjectId, language: langCode() } }))}
        exitHref="/learn/"
        doneHref="/learn/"
      />
    );

  return (
    <div className="mx-auto flex min-h-dvh max-w-xl flex-col gap-6 px-4 py-8">
      <div className="flex items-center gap-3">
        <ProgressBar value={step} max={TOTAL} label={t("onb.step", { n: step, total: TOTAL })} />
        <span className="shrink-0 text-sm text-ink-soft">{t("onb.step", { n: step, total: TOTAL })}</span>
      </div>
      <Mascot mood="thinking" size={120} alt={t("mascot.alt")} className="mx-auto h-auto w-28" />

      {step === 1 && (
        <>
          <h1 className="text-center text-3xl">{t("onb.title.target")}</h1>
          <section className="flex flex-col gap-2">
            <h2 className="text-sm uppercase text-ink-soft">{t("onb.language")}</h2>
            <AsyncView state={languages.state} onRetry={languages.reload} isEmpty={(d) => d.length === 0}>
              {(d) => (
                <div className="grid grid-cols-2 gap-2">
                  {d.map((l) => (
                    <Choice key={l.id} on={languageId === l.id} onClick={() => setLanguageId(l.id)}>
                      {pick(l.names, locale)}
                    </Choice>
                  ))}
                </div>
              )}
            </AsyncView>
          </section>
          <section className="flex flex-col gap-2">
            <h2 className="text-sm uppercase text-ink-soft">{t("onb.lyceum")}</h2>
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("lyceums.search")}
              aria-label={t("lyceums.search")}
              className="w-full rounded-2xl border-2 border-line bg-snow px-4 py-3 text-ink focus:border-blue focus:bg-white"
            />
            <AsyncView state={lyceums.state} onRetry={lyceums.reload} isEmpty={(d) => d.length === 0}>
              {(d) => (
                <div className="flex max-h-72 flex-col gap-2 overflow-y-auto">
                  {d
                    .filter((l) => !q.trim() || pick(l.names, locale).toLowerCase().includes(q.trim().toLowerCase()))
                    .map((l) => (
                      <Choice key={l.id} on={lyceumId === l.id} onClick={() => setLyceumId(l.id)}>
                        {pick(l.names, locale)}
                      </Choice>
                    ))}
                </div>
              )}
            </AsyncView>
          </section>
          <Button block disabled={!lyceumId || !languageId} onClick={() => setStep(2)}>
            {t("common.continue")}
          </Button>
        </>
      )}

      {step === 2 && (
        <>
          <h1 className="text-center text-3xl">{t("onb.title.subjects")}</h1>
          <AsyncView state={subjects.state} onRetry={subjects.reload} isEmpty={(d) => d.length === 0}>
            {(d) => (
              <div className="grid gap-2 sm:grid-cols-2">
                {d.map((s) => (
                  <Choice key={s.id} on={subjectId === s.id} onClick={() => setSubjectId(s.id)}>
                    {pick(s.names, locale)}
                  </Choice>
                ))}
              </div>
            )}
          </AsyncView>
          <Card className="text-center">
            <h2 className="text-xl">{t("onb.title.placement")}</h2>
            <p className="text-ink-soft">{t("onb.placement.text")}</p>
            {isGuest && <p className="mt-1 text-sm text-ink-soft">{t("onb.guestNote")}</p>}
          </Card>
          {saveError && (
            <p role="alert" className="font-bold text-red-deep">
              {t("common.error")}
            </p>
          )}
          <div className="flex flex-col gap-3">
            <Button block disabled={!subjectId || busy} onClick={startTest}>
              {t("onb.placement.start")}
            </Button>
            <Button block variant="secondary" disabled={busy} onClick={skip}>
              {t("onb.placement.skip")}
            </Button>
            <Button variant="ghost" onClick={() => setStep(1)}>
              {t("common.back")}
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
