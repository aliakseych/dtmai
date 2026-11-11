"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useLocale, useT } from "@dtmai/i18n";
import { LessonPlayer } from "@/components/lesson/LessonPlayer";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";
import { LanguageStep } from "./LanguageStep";
import { LyceumStep } from "./LyceumStep";
import { OnboardingFrame } from "./OnboardingFrame";
import { PlacementStep } from "./PlacementStep";
import { CityStep, type CityChoice } from "./CityStep";
import { fetchCities } from "@/lib/cities";
import { SubjectsStep } from "./SubjectsStep";
import { FieldStep } from "./FieldStep";
import { PrioritiesStep } from "./PrioritiesStep";
import { fetchFields } from "@/lib/fields";

const STEPS = ["city", "language", "lyceum", "field", "priorities", "subjects", "placement"] as const;

/** City -> language -> first lyceum -> field -> other priorities -> subjects (derived from the field) -> placement. */
export function Onboarding() {
  const t = useT();
  const { locale } = useLocale();
  const router = useRouter();
  const { isGuest, reloadMe } = useAuth();
  const [i, setI] = useState(0);
  const [city, setCity] = useState<CityChoice>(undefined);
  const [lyceumIds, setLyceumIds] = useState<string[]>([]);
  const [languageId, setLanguageId] = useState<string | null>(null);
  const [subjectIds, setSubjectIds] = useState<string[]>([]);
  const [fieldCode, setFieldCode] = useState<string | null>(null);
  const [placing, setPlacing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [saveError, setSaveError] = useState(false);

  const lyceums = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums", { params: { query: { limit: 200 } } })), []);
  const languages = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums/languages")), []);
  const subjects = useAsync(() => api.unwrap(api.client.GET("/v1/catalog/subjects")), []);

  const cities = useAsync(fetchCities, []);
  const fields = useAsync(fetchFields, []);
  const fieldList = fields.state.status === "ready" ? fields.state.data : [];
  const chosenField = fieldList.find((f) => f.code === fieldCode);
  // Subjects are fixed by the field's mapping; editable only when it has none.
  const subjectsLocked = !!chosenField && chosenField.subject_ids.length > 0;
  const lyceumRows = lyceums.state.status === "ready" ? lyceums.state.data : [];
  const offered = lyceumRows.find((l) => l.id === lyceumIds[0])?.field_codes ?? [];

  const subjectList = subjects.state.status === "ready" ? subjects.state.data : [];
  // First subject in catalog order among those chosen.
  const firstSubject = subjectList.find((s) => subjectIds.includes(s.id));
  const langCode = () => {
    const c = languages.state.status === "ready" ? languages.state.data.find((l) => l.id === languageId)?.code : undefined;
    return c === "ru" || c === "en" ? c : "uz";
  };

  async function save(): Promise<boolean> {
    if (lyceumIds.length === 0 || !languageId) return false;
    setBusy(true);
    setSaveError(false);
    try {
      await api.unwrap(
        api.client.PATCH("/v1/identity/me", {
          body: { city: city ?? null, subject_ids: subjectIds, dream_lyceum_ids: lyceumIds, education_language_id: languageId, field_code: fieldCode },
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
        <OnboardingFrame {...frame} speech={t("onb.city.q")} canContinue={city !== undefined || cities.state.status === "error"}>
          <CityStep state={cities.state} onRetry={cities.reload} value={city} onChange={setCity} />
        </OnboardingFrame>
      )}
      {step === "language" && (
        <OnboardingFrame {...frame} speech={t("onb.language.q")} mood="straight" canContinue={!!languageId}>
          <LanguageStep state={languages.state} onRetry={languages.reload} value={languageId} onChange={setLanguageId} />
        </OnboardingFrame>
      )}
      {step === "lyceum" && (
        <OnboardingFrame {...frame} speech={t("onb.title.target")} canContinue={lyceumIds.length > 0}>
          <LyceumStep
            single
            state={lyceums.state}
            onRetry={lyceums.reload}
            city={city ?? null}
            value={lyceumIds.slice(0, 1)}
            onChange={(ids) => {
              setLyceumIds((cur) => (ids[0] && cur[0] !== ids[0] ? [ids[0], ...cur.slice(1).filter((x) => x !== ids[0])] : cur));
              if (ids[0] !== lyceumIds[0]) setFieldCode(null);
            }}
          />
        </OnboardingFrame>
      )}
      {step === "field" && (
        <OnboardingFrame {...frame} speech={t("onb.title.field")} canContinue={!!fieldCode || (fields.state.status === "ready" && offered.every((c) => !fieldList.some((f) => f.code === c)))}>
          <FieldStep
            state={fields.state}
            onRetry={fields.reload}
            offered={offered}
            value={fieldCode}
            onChange={(code) => {
              setFieldCode(code);
              const f = fieldList.find((x) => x.code === code);
              if (f && f.subject_ids.length > 0) setSubjectIds(f.subject_ids);
            }}
          />
        </OnboardingFrame>
      )}
      {step === "priorities" && (
        <OnboardingFrame {...frame} speech={t("onb.title.priorities")} canContinue={lyceumIds.length > 0}>
          <PrioritiesStep state={lyceums.state} onRetry={lyceums.reload} city={city ?? null} value={lyceumIds} onChange={setLyceumIds} fieldCode={fieldCode} />
        </OnboardingFrame>
      )}
      {step === "subjects" && (
        <OnboardingFrame {...frame} speech={t("onb.title.subjects")} canContinue={subjectIds.length > 0}>
          <SubjectsStep state={subjects.state} onRetry={subjects.reload} value={subjectIds} onToggle={toggleSubject} readOnly={subjectsLocked} />
        </OnboardingFrame>
      )}
    </>
  );
}
