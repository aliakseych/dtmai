"use client";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useLocale, useT } from "@dtmai/i18n";
import { LessonPlayer } from "@/components/lesson/LessonPlayer";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";
import { CityStep } from "./CityStep";
import { LanguageStep } from "./LanguageStep";
import { LyceumStep } from "./LyceumStep";
import { OnboardingFrame } from "./OnboardingFrame";
import { PlacementStep } from "./PlacementStep";
import { SubjectsStep } from "./SubjectsStep";
import { normCity, type OnbLyceum } from "./types";

const STEPS = ["city", "language", "lyceum", "subjects", "placement"] as const;

/** City -> education language -> dream lyceum -> subjects (multi) -> placement for the first subject. */
export function Onboarding() {
  const t = useT();
  const { locale } = useLocale();
  const router = useRouter();
  const { isGuest, reloadMe } = useAuth();
  const [i, setI] = useState(0);
  const [city, setCity] = useState("");
  const [lyceumId, setLyceumId] = useState<string | null>(null);
  const [languageId, setLanguageId] = useState<string | null>(null);
  const [subjectIds, setSubjectIds] = useState<string[]>([]);
  const [placing, setPlacing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [saveError, setSaveError] = useState(false);

  const lyceums = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums", { params: { query: { limit: 200 } } })) as Promise<OnbLyceum[]>, []);
  const languages = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums/languages")), []);
  const subjects = useAsync(() => api.unwrap(api.client.GET("/v1/catalog/subjects")), []);

  const cities = useMemo(() => {
    if (lyceums.state.status !== "ready") return [];
    const seen = new Map<string, string>();
    for (const l of lyceums.state.data) if (l.city?.trim()) seen.set(normCity(l.city), l.city.trim());
    return [...seen.values()].sort((a, b) => a.localeCompare(b));
  }, [lyceums.state]);

  const subjectList = subjects.state.status === "ready" ? subjects.state.data : [];
  // First subject in catalog order among those chosen.
  const firstSubject = subjectList.find((s) => subjectIds.includes(s.id));
  const langCode = () => {
    const c = languages.state.status === "ready" ? languages.state.data.find((l) => l.id === languageId)?.code : undefined;
    return c === "ru" || c === "en" ? c : "uz";
  };

  async function save(): Promise<boolean> {
    if (!lyceumId || !languageId) return false;
    setBusy(true);
    setSaveError(false);
    try {
      await api.unwrap(
        api.client.PATCH("/v1/identity/me", {
          body: { city: city.trim() || null, subject_ids: subjectIds, target_lyceum_id: lyceumId, education_language_id: languageId },
        }),
      );
      await reloadMe();
      return true;
    } catch {
      setSaveError(true);
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function start() {
    if (await save()) setPlacing(true);
  }

  /** Placement is optional: skipping records it so the path starts at unit 0. */
  async function skip() {
    if (!(await save())) return;
    try {
      if (firstSubject) await api.unwrap(api.client.POST("/v1/learning/placement/{subject_id}/skip", { params: { path: { subject_id: firstSubject.id } } }));
    } catch {
      /* skipping is best-effort; the path is reachable regardless */
    }
    router.replace("/learn/");
  }

  if (placing && firstSubject)
    return (
      <LessonPlayer
        load={() => api.unwrap(api.client.POST("/v1/learning/placement/start", { body: { subject_id: firstSubject.id, language: langCode() } }))}
        exitHref="/learn/"
        doneHref="/learn/"
      />
    );

  const step = STEPS[i]!;
  const next = () => setI((n) => n + 1);
  const back = i > 0 ? () => setI((n) => n - 1) : undefined;
  const toggleSubject = (id: string) => setSubjectIds((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  if (step === "placement")
    return <PlacementStep subjectName={firstSubject ? pick(firstSubject.names, locale) : ""} busy={busy} error={saveError} isGuest={isGuest} onStart={start} onSkip={skip} onBack={() => setI(i - 1)} />;

  const frame = { stepKey: step, step: i + 1, total: STEPS.length, onBack: back, onContinue: next };
  return (
    <>
      {step === "city" && (
        <OnboardingFrame {...frame} speech={t("onb.city.q")} canContinue={city.trim().length > 0 || (lyceums.state.status === "error")}>
          <CityStep cities={cities} value={city} onChange={setCity} />
        </OnboardingFrame>
      )}
      {step === "language" && (
        <OnboardingFrame {...frame} speech={t("onb.language.q")} mood="straight" canContinue={!!languageId}>
          <LanguageStep state={languages.state} onRetry={languages.reload} value={languageId} onChange={setLanguageId} />
        </OnboardingFrame>
      )}
      {step === "lyceum" && (
        <OnboardingFrame {...frame} speech={t("onb.title.target")} canContinue={!!lyceumId}>
          <LyceumStep state={lyceums.state} onRetry={lyceums.reload} city={city} value={lyceumId} onChange={setLyceumId} />
        </OnboardingFrame>
      )}
      {step === "subjects" && (
        <OnboardingFrame {...frame} speech={t("onb.title.subjects")} canContinue={subjectIds.length > 0}>
          <SubjectsStep state={subjects.state} onRetry={subjects.reload} value={subjectIds} onToggle={toggleSubject} />
        </OnboardingFrame>
      )}
    </>
  );
}
