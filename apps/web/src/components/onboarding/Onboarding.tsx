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
import { hasContent } from "@/components/practice/SubjectEmpty";
import { FieldStep } from "./FieldStep";
import { PrioritiesStep } from "./PrioritiesStep";
import { fetchFields } from "@/lib/fields";

const STEPS = ["city", "language", "field", "lyceum", "priorities", "placement"] as const;

/** City -> language -> field (shown as its subjects; they are derived from it) -> first lyceum -> other priorities -> placement -> plan -> account. */
export function Onboarding() {
  const t = useT();
  const { locale } = useLocale();
  const router = useRouter();
  const { isGuest, reloadMe, me } = useAuth();
  // Resume: prefill from the saved profile and open the first unanswered step.
  const [i, setI] = useState(() => (!me?.city ? 0 : !me.education_language_id ? 1 : !me.field_code ? 2 : me.dream_lyceum_ids.length === 0 ? 3 : 5));
  const [city, setCity] = useState<CityChoice>(me?.city ?? undefined);
  const [lyceumIds, setLyceumIds] = useState<string[]>(me?.dream_lyceum_ids ?? []);
  const [languageId, setLanguageId] = useState<string | null>(me?.education_language_id ?? null);
  const [subjectIds, setSubjectIds] = useState<string[]>(me?.subject_ids ?? []);
  const [fieldCode, setFieldCode] = useState<string | null>(me?.field_code ?? null);
  const [placing, setPlacing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [saveError, setSaveError] = useState(false);

  const lyceums = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums", { params: { query: { limit: 200 } } })), []);
  const languages = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums/languages")), []);
  const subjects = useAsync(() => api.unwrap(api.client.GET("/v1/catalog/subjects")), []);

  const cities = useAsync(fetchCities, []);
  const fields = useAsync(fetchFields, []);
  const fieldList = fields.state.status === "ready" ? fields.state.data : [];

  const subjectList = subjects.state.status === "ready" ? subjects.state.data : [];
  // First chosen subject in catalog order, preferring one that has questions (placement needs content).
  const chosen = subjectList.filter((s) => subjectIds.includes(s.id));
  const firstSubject = chosen.find(hasContent) ?? chosen[0];
  const placementEmpty = !!firstSubject && !hasContent(firstSubject);
  // Education-language codes are numeric (11 Uzbek, 12 Russian, 14 English); the placement API takes uz/ru/en.
  const langCode = () => {
    const c = languages.state.status === "ready" ? languages.state.data.find((l) => l.id === languageId)?.code : undefined;
    return c === "12" ? "ru" : c === "14" ? "en" : "uz";
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
    router.replace("/plan/setup/");
  }

  if (placing && firstSubject && !placementEmpty)
    return (
      <LessonPlayer
        load={() => api.unwrap(api.client.POST("/v1/learning/placement/start", { body: { subject_id: firstSubject.id, language: langCode() } }))}
        exitHref="/home/"
        doneHref="/plan/setup/"
      />
    );

  const step = STEPS[i]!;
  const next = () => setI((n) => n + 1);
  const back = i > 0 ? () => setI((n) => n - 1) : undefined;

  if (step === "placement")
    return <PlacementStep subjectName={firstSubject ? pick(firstSubject.names, locale) : ""} noContent={placementEmpty} busy={busy} error={saveError} isGuest={isGuest} onStart={start} onSkip={skip} onBack={() => setI(i - 1)} />;

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
            }}
          />
        </OnboardingFrame>
      )}
      {step === "field" && (
        <OnboardingFrame {...frame} speech={t("onb.title.field")} canContinue={!!fieldCode || fields.state.status === "error"}>
          <FieldStep
            state={fields.state}
            onRetry={fields.reload}
            subjectNames={new Map(subjectList.map((s) => [s.id, s.names]))}
            value={fieldCode}
            onChange={(code) => {
              setFieldCode(code);
              const f = fieldList.find((x) => x.code === code);
              if (!f) return;
              // Subjects come from the field; one without a mapping falls back to the subjects that have content.
              const ready = subjectList.filter(hasContent);
              setSubjectIds(f.subject_ids.length > 0 ? f.subject_ids : (ready.length > 0 ? ready : subjectList.slice(0, 1)).map((x) => x.id));
            }}
          />
        </OnboardingFrame>
      )}
      {step === "priorities" && (
        <OnboardingFrame {...frame} speech={t("onb.title.priorities")} canContinue={lyceumIds.length > 0}>
          <PrioritiesStep state={lyceums.state} onRetry={lyceums.reload} city={city ?? null} value={lyceumIds} onChange={setLyceumIds} fieldCode={fieldCode} />
        </OnboardingFrame>
      )}
    </>
  );
}
