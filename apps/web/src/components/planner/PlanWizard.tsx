"use client";
import { useCallback, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Button, cn, LockIcon, Icon } from "@dtmai/ui";
import { useLocale, useT, type MessageKey } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { useSubjectNames } from "@/components/mocks/useSubjectNames";
import { OnboardingFrame } from "@/components/onboarding/OnboardingFrame";
import { Choice } from "@/components/onboarding/Choice";
import { useAuth, useLearnLanguage } from "@/lib/auth";
import { fetchFields } from "@/lib/fields";
import { addDays, clampMinutes, datesError, formatDay, MAX_DAY_MINUTES, MIN_LEAD_DAYS, todayISO, type DatesError } from "@/lib/planDates";
import { getSettings, listProfiles, profileName, saveSettings, type CertRule, type Certificate, type ExamProfile, type ExamSection as Section } from "@/lib/planner";
import { useAsync } from "@/lib/useAsync";
import { GeneratingScreen } from "./GeneratingScreen";
import { StudyTimeStep } from "./StudyTimeStep";

const STEPS = ["field", "cert", "days", "dates", "study", "review"] as const;
type StepKey = (typeof STEPS)[number];

/** `/plan/setup`: field -> certificates -> minutes -> dates -> review -> generating. Saving settings rebuilds the plan. */
export function PlanWizard() {
  const t = useT();
  const { locale } = useLocale();
  const learnLang = useLearnLanguage();
  const router = useRouter();
  const { me } = useAuth();
  const profiles = useAsync(listProfiles, []);
  const { name: subjectName } = useSubjectNames();
  const fields = useAsync(fetchFields, []);
  const today = todayISO();

  const [i, setI] = useState(0);
  const [code, setCode] = useState<string | null>(null);
  const [choices, setChoices] = useState<Record<string, string>>({});
  const [rules, setRules] = useState<Record<string, string | null>>({});
  const [school, setSchool] = useState(45);
  const [weekend, setWeekend] = useState(90);
  const [start, setStart] = useState(today);
  const [exam, setExam] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [studyTime, setStudyTime] = useState("");
  const [studyDays, setStudyDays] = useState<number[]>([]);

  const list = useMemo(() => (profiles.state.status === "ready" ? profiles.state.data.filter((p) => p.kind === "academic_lyceum") : []), [profiles.state]);
  const prefill = me?.field_code ? list.find((p) => p.direction_code === me.field_code || p.code === me.field_code)?.code : undefined;
  const profile = list.find((p) => p.code === (code ?? prefill));
  const fieldRows = fields.state.status === "ready" ? fields.state.data : [];
  // Same label as onboarding: the field name plus its subjects, never the opaque profile code.
  const fieldLabel = (p: ExamProfile) => {
    const f = fieldRows.find((x) => x.code === (p.direction_code ?? p.code));
    return {
      name: f?.name ?? profileName(p, locale),
      subjects: f ? f.subject_ids.map((id) => subjectName(id)).filter(Boolean).join(" · ") : "",
    };
  };
  // Onboarding already chose the field: no list, and the whole step goes away unless a subject choice is still open.
  const fieldFixed = !!prefill && code === null;
  const needsChoice = !!profile && profile.sections.some((s) => s.choice_group);
  const examDate = exam ?? profile?.exam_date ?? "";

  const sectionName = (s: Section) => {
    if (s.role === "iq") return t("plan.wizard.iq");
    if (s.role === "creative") return t("plan.wizard.creative");
    const id = s.choice_group ? choices[s.id] : s.subject_id;
    if (id) return subjectName(id);
    return s.choice_group ? t("plan.wizard.chooseLanguage") : t("common.soon");
  };

  const certificates = (): Certificate[] =>
    !profile
      ? []
      : Object.entries(rules).flatMap(([sectionId, ruleId]) => {
          const r = profile.certificate_rules.find((x) => x.id === ruleId && x.section_id === sectionId);
          return r && r.min_value !== null ? [{ section_id: sectionId, cert_type: r.cert_type, value: r.min_value, language_subject_id: r.language_subject_id }] : [];
        });

  const dateErr = datesError(today, start, examDate);
  const valid: Record<StepKey, boolean> = {
    field: !!profile && profile.sections.filter((s) => s.choice_group).every((s) => !!choices[s.id]),
    cert: true,
    days: true,
    dates: dateErr === null,
    study: true,
    review: true,
  };
  // The certificate question only applies when the track has an exemptible subject with accepted certificates.
  const hasCert = !profile || profile.sections.some((s) => s.exemptible && s.role === "subject" && profile.certificate_rules.some((r) => r.section_id === s.id && r.min_value !== null));
  const steps = STEPS.filter((s) => (s !== "cert" || hasCert) && (s !== "field" || !fieldFixed || needsChoice));
  const key = steps[i]!;

  const request = useCallback(async () => {
    if (!profile) throw new Error("no profile");
    const prev = await getSettings();
    return saveSettings({
      direction_code: profile.direction_code ?? profile.code,
      language: learnLang === "ru" ? "ru" : "uz",
      start_date: start,
      exam_date: examDate,
      minutes_school_day: school,
      minutes_weekend_day: weekend,
      choice_subject_id: Object.values(choices)[0] ?? null,
      certificates: certificates(),
      target_lyceum_ids: prev?.target_lyceum_ids ?? [],
      study_time: studyTime || prev?.study_time || null,
      study_days: studyDays.length ? studyDays : (prev?.study_days ?? []),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [generating]);
  const done = useCallback(() => router.replace("/plan/"), [router]);

  if (generating) return <GeneratingScreen request={request} onDone={done} onBack={() => setGenerating(false)} />;

  return (
    <AsyncView state={profiles.state} onRetry={profiles.reload} isEmpty={() => list.length === 0} emptyText={t("plan.wizard.noProfiles")}>
      {() => (
        <OnboardingFrame
          stepKey={key}
          step={i + 1}
          total={steps.length}
          speech={key === "field" && fieldFixed ? t("plan.wizard.choice.speech") : t(`plan.wizard.${key}.speech`)}
          mood={key === "review" ? "celebrate" : "calendar"}
          onBack={() => (i === 0 ? router.back() : setI(i - 1))}
          onContinue={() => (key === "review" ? setGenerating(true) : setI(i + 1))}
          canContinue={valid[key]}
          continueLabel={key === "review" ? t("plan.wizard.generate") : undefined}
        >
          {key === "field" && (
            <FieldStep fixed={fieldFixed} label={fieldLabel} list={list} selected={profile?.code} onPick={(c) => { setCode(c); setChoices({}); setRules({}); setExam(null); }} profile={profile} sectionName={sectionName} choices={choices} setChoices={setChoices} subjectName={subjectName} />
          )}
          {key === "cert" && profile && <CertStep profile={profile} choices={choices} rules={rules} setRules={setRules} sectionName={sectionName} />}
          {key === "days" && <DaysStep school={school} setSchool={setSchool} weekend={weekend} setWeekend={setWeekend} />}
          {key === "dates" && profile && <DatesStep profile={profile} today={today} start={start} setStart={setStart} exam={examDate} setExam={setExam} err={dateErr} />}
          {key === "study" && <StudyTimeStep time={studyTime} setTime={setStudyTime} days={studyDays} setDays={setStudyDays} />}
          {key === "review" && profile && (
            <ReviewStep
              profile={profile}
              title={fieldLabel(profile).name}
              sectionName={sectionName}
              exempt={certificates().map((c) => c.section_id)}
              rows={[
                [t("plan.wizard.days.school"), `${school} ${t("plan.min")}`],
                [t("plan.wizard.days.weekend"), `${weekend} ${t("plan.min")}`],
                [t("plan.wizard.dates.start"), formatDay(start, locale, { day: "numeric", month: "long", year: "numeric" })],
                [t("plan.wizard.dates.exam"), formatDay(examDate, locale, { day: "numeric", month: "long", year: "numeric" })],
              ]}
            />
          )}
        </OnboardingFrame>
      )}
    </AsyncView>
  );
}

function SectionRow({ s, label, exempt }: { s: Section; label: string; exempt?: boolean }) {
  const t = useT();
  const inApp = s.available;
  return (
    <li className="flex items-center justify-between gap-3 rounded-xl border-2 border-line bg-white px-3 py-2">
      <span className="min-w-0">
        <span className="block break-words font-extrabold">{label}</span>
        {!inApp && <span className="block text-sm font-bold text-ink-soft">{t("plan.wizard.notInApp")}</span>}
        {exempt && <span className="block text-sm font-bold text-accent-deep">{t("plan.exemptCertificate")}</span>}
        {inApp && s.question_count !== null && <span className="block text-sm text-ink-soft">{t("plan.wizard.questions", { n: s.question_count })}</span>}
      </span>
      <span className="shrink-0 rounded-lg bg-snow px-2 py-1 text-sm font-extrabold">{t("plan.wizard.points", { n: s.max_points })}</span>
    </li>
  );
}

function FieldStep({
  fixed,
  label,
  list,
  selected,
  onPick,
  profile,
  sectionName,
  choices,
  setChoices,
  subjectName,
}: {
  fixed: boolean;
  label: (p: ExamProfile) => { name: string; subjects: string };
  list: ExamProfile[];
  selected: string | undefined;
  onPick: (code: string) => void;
  profile: ExamProfile | undefined;
  sectionName: (s: Section) => string;
  choices: Record<string, string>;
  setChoices: (c: Record<string, string>) => void;
  subjectName: (id: string) => string;
}) {
  const t = useT();
  return (
    <>
      {!fixed && <p className="text-ink-soft">{t("plan.wizard.field.hint")}</p>}
      {!fixed && <div role="radiogroup" aria-label={t("plan.wizard.field.speech")} className="flex flex-col gap-2">
        {list.map((p) => (
          <Choice key={p.code} on={p.code === selected} onClick={() => onPick(p.code)}>
            <span className="min-w-0 flex-1">
              <span className="block break-words">{label(p).name}</span>
              {label(p).subjects && <span className="block text-sm font-bold text-ink-soft">{label(p).subjects}</span>}
              {p.sections.some((s) => !s.available) && <span className="mt-1 inline-block rounded-lg bg-snow px-2 py-0.5 text-sm font-bold text-ink-soft">{t("plan.wizard.partialSubjects")}</span>}
            </span>
          </Choice>
        ))}
      </div>}
      {profile && (
        <section aria-label={t("plan.wizard.exam")} className="flex flex-col gap-2">
          <h2 className="text-sm uppercase text-ink-soft">{t("plan.wizard.exam")}</h2>
          <ul className="flex flex-col gap-2">
            {profile.sections.map((s) => (
              <SectionRow key={s.id} s={s} label={sectionName(s)} />
            ))}
          </ul>
          <p className="text-sm font-extrabold text-ink-soft">{t("plan.wizard.total", { n: profile.max_score })}</p>
          {!profile.verified && <p className="text-sm font-bold text-ink-soft">{t("plan.unverified")}</p>}
          {profile.sections
            .filter((s) => s.choice_group)
            .map((s) => (
              <div key={s.id} className="flex flex-col gap-2" role="radiogroup" aria-label={t("plan.wizard.chooseLanguage")}>
                <h3 className="text-sm uppercase text-ink-soft">{t("plan.wizard.chooseLanguage")}</h3>
                <div className="flex flex-wrap gap-2">
                  {(profile.choices[s.choice_group!] ?? []).map((id) => (
                    <button
                      key={id}
                      type="button"
                      role="radio"
                      aria-checked={choices[s.id] === id}
                      onClick={() => setChoices({ ...choices, [s.id]: id })}
                      className={cn(
                        "rounded-xl border-2 border-b-4 px-3 py-2 font-extrabold",
                        choices[s.id] === id ? "border-brand bg-brand-soft text-brand" : "border-line bg-white",
                      )}
                    >
                      {subjectName(id)}
                    </button>
                  ))}
                </div>
              </div>
            ))}
        </section>
      )}
    </>
  );
}

function CertStep({
  profile,
  choices,
  rules,
  setRules,
  sectionName,
}: {
  profile: ExamProfile;
  choices: Record<string, string>;
  rules: Record<string, string | null>;
  setRules: (r: Record<string, string | null>) => void;
  sectionName: (s: Section) => string;
}) {
  const t = useT();
  const { locale } = useLocale();
  const iq = profile.sections.filter((s) => s.role === "iq" || !s.exemptible);
  const open = profile.sections.filter((s) => s.exemptible && s.role === "subject");
  const certLabel = (r: CertRule) => [r.cert_type === "national" || r.cert_type === "other_intl" ? t(`plan.cert.${r.cert_type}`) : r.cert_type.toUpperCase(), r.level_label].filter(Boolean).join(" ");
  return (
    <>
      <p className="text-ink-soft">{t("plan.wizard.cert.hint")}</p>
      {open.map((s) => {
        const lang = s.choice_group ? choices[s.id] : s.subject_id;
        const opts = profile.certificate_rules.filter((r) => r.section_id === s.id && r.min_value !== null && (!r.language_subject_id || r.language_subject_id === lang));
        return (
          <section key={s.id} className="flex flex-col gap-2" aria-label={sectionName(s)}>
            <h2 className="text-lg">{sectionName(s)}</h2>
            <div role="radiogroup" aria-label={sectionName(s)} className="flex flex-col gap-2">
              <Choice on={!rules[s.id]} onClick={() => setRules({ ...rules, [s.id]: null })}>
                {t("plan.wizard.cert.none")}
              </Choice>
              {opts.map((r) => (
                <Choice key={r.id} on={rules[s.id] === r.id} onClick={() => setRules({ ...rules, [s.id]: r.id })}>
                  <span className="min-w-0 flex-1">
                    <span className="block break-words">{certLabel(r)}</span>
                    {(r.note[locale] || !r.verified) && <span className="block text-sm font-bold text-ink-soft">{r.note[locale] || t("plan.unverified")}</span>}
                  </span>
                </Choice>
              ))}
            </div>
            {opts.length === 0 && <p className="text-sm text-ink-soft">{t("plan.wizard.cert.noneAvailable")}</p>}
          </section>
        );
      })}
      {iq.map((s) => (
        <div key={s.id} className="flex items-center gap-3 rounded-2xl border-2 border-line bg-snow px-4 py-3">
          <LockIcon />
          <span className="font-extrabold">
            {sectionName(s)}: {t("plan.wizard.cert.iqLocked")}
          </span>
        </div>
      ))}
    </>
  );
}

function Stepper({ label, value, onChange }: { label: string; value: number; onChange: (n: number) => void }) {
  const t = useT();
  return (
    <div className="flex items-center justify-between gap-3 rounded-2xl border-2 border-line bg-white px-4 py-3">
      <span className="min-w-0 font-extrabold">{label}</span>
      <span className="flex shrink-0 items-center gap-2">
        <Button variant="secondary" aria-label={`${label}: ${t("common.decrease")}`} onClick={() => onChange(clampMinutes(value - 5))} className="min-h-11 min-w-11 px-3 py-1">
          <Icon name="minus" size={20} />
        </Button>
        <output className="min-w-16 text-center text-lg font-extrabold">
          {value} {t("plan.min")}
        </output>
        <Button variant="secondary" aria-label={`${label}: ${t("common.increase")}`} onClick={() => onChange(clampMinutes(value + 5))} className="min-h-11 min-w-11 px-3 py-1">
          <Icon name="plus" size={20} />
        </Button>
      </span>
    </div>
  );
}

function DaysStep(p: { school: number; setSchool: (n: number) => void; weekend: number; setWeekend: (n: number) => void }) {
  const t = useT();
  return (
    <>
      <Stepper label={t("plan.wizard.days.school")} value={p.school} onChange={p.setSchool} />
      <Stepper label={t("plan.wizard.days.weekend")} value={p.weekend} onChange={p.setWeekend} />
      <p className="text-sm text-ink-soft">{t("plan.wizard.days.max", { n: MAX_DAY_MINUTES })}</p>
    </>
  );
}

function DatesStep({
  profile,
  today,
  start,
  setStart,
  exam,
  setExam,
  err,
}: {
  profile: ExamProfile;
  today: string;
  start: string;
  setStart: (d: string) => void;
  exam: string;
  setExam: (d: string) => void;
  err: DatesError | null;
}) {
  const t = useT();
  const { locale } = useLocale();
  const input = "rounded-2xl border-2 border-line bg-white px-4 py-3 font-extrabold";
  return (
    <>
      <label className="flex flex-col gap-1">
        <span className="text-sm uppercase text-ink-soft">{t("plan.wizard.dates.start")}</span>
        <input type="date" min={today} value={start} onChange={(e) => setStart(e.target.value)} className={input} />
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-sm uppercase text-ink-soft">{t("plan.wizard.dates.exam")}</span>
        <input type="date" min={start ? addDays(start, MIN_LEAD_DAYS) : undefined} value={exam} onChange={(e) => setExam(e.target.value)} className={input} />
      </label>
      {!profile.date_verified && <p className="text-sm font-bold text-ink-soft">{t("plan.wizard.dates.unverified")}</p>}
      {err && (
        <p role="alert" className="font-bold text-red-deep">
          {err === "start_past" ? t("plan.wizard.dates.startPast") : t("plan.wizard.dates.tooSoon", { n: MIN_LEAD_DAYS })}
        </p>
      )}
      {!err && exam && <p className="rounded-xl bg-accent-soft px-3 py-2 font-bold">{t("plan.wizard.dates.end", { date: formatDay(addDays(exam, -profile.taper_days), locale), n: profile.taper_days })}</p>}
    </>
  );
}

function ReviewStep({ profile, title, sectionName, exempt, rows }: { profile: ExamProfile; title: string; sectionName: (s: Section) => string; exempt: string[]; rows: [string, string][] }) {
  const t = useT();
  return (
    <>
      <h2 className="text-xl">{title}</h2>
      <ul className="flex flex-col gap-2">
        {profile.sections.map((s) => (
          <SectionRow key={s.id} s={s} label={sectionName(s)} exempt={exempt.includes(s.id)} />
        ))}
      </ul>
      <dl className="flex flex-col divide-y-2 divide-line rounded-card border-2 border-line bg-white">
        {rows.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-3 px-4 py-2">
            <dt className="text-ink-soft">{k}</dt>
            <dd className="min-w-0 break-words text-right font-extrabold">{v}</dd>
          </div>
        ))}
      </dl>
      <p className="text-sm text-ink-soft">{t("plan.wizard.review.hint")}</p>
    </>
  );
}
