"use client";
import { useEnum, useT } from "@/lib/i18n";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useAct, useSubjects } from "@/lib/catalog";
import { examInfo, type CertRule, type EventIn, type ExamEvent, type ExamProfile, type Faq, type FaqIn } from "@/lib/examInfo";
import { fieldErrors, nm, type Names } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader, Select, Tabs } from "@/components/ui/controls";
import { cleanNames, NamesEditor } from "@/components/ui/names";
import { useConfirm } from "@/components/ui/confirm";
import { DataTable } from "@/components/ui/table";

type Tab = "faq" | "events" | "profiles";
const FAQ_KEY = ["exam-info-faq"];
const EVT_KEY = ["exam-info-events"];
const PRO_KEY = ["exam-info-profiles"];
const EVENT_KINDS = ["applications", "test", "results", "appeal"];
const CERT_TYPES = ["cefr", "ielts", "toefl", "national", "other_intl"];
const Panel = ({ children }: { children: React.ReactNode }) => (
  <div className="space-y-3 rounded-xl border border-line bg-white p-4">{children}</div>
);

export default function ExamInfoPage() {
  const t = useT();
  const en = useEnum();
  const [tab, setTab] = useState<Tab>("faq");
  return (
    <>
      <PageHeader title={t("admin.examInfo.examInfo")} sub={t("admin.examInfo.examRulesDatesFaq")} />
      <Tabs value={tab} onChange={setTab} items={[{ id: "faq", label: t("admin.examInfo.faq") }, { id: "events", label: t("admin.examInfo.dates") }, { id: "profiles", label: t("admin.examInfo.directionsCertificates") }]} />
      <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">
        {tab === "faq" && <FaqTab />}
        {tab === "events" && <EventsTab />}
        {tab === "profiles" && <ProfilesTab />}
      </div>
    </>
  );
}

// --- FAQ ---------------------------------------------------------------------------
const emptyFaq = (): FaqIn => ({ key: "", category: "general", question: {}, answer: {}, position: 0, published: true, verified: false, source_url: null });

function FaqTab() {
  const t = useT();
  const en = useEnum();
  const [ask, confirmNode] = useConfirm();
  const q = useQuery({ queryKey: FAQ_KEY, queryFn: () => examInfo.faq.list() });
  const [draft, setDraft] = useState<{ id: string | null; body: FaqIn } | null>(null);
  const save = useAct((a: { id: string | null; body: FaqIn }) => (a.id ? examInfo.faq.update(a.id, a.body) : examInfo.faq.create(a.body)), [FAQ_KEY], t("admin.examInfo.faqSaved"));
  const del = useAct((id: string) => examInfo.faq.remove(id), [FAQ_KEY], t("admin.examInfo.faqDeleted"));
  const fe = fieldErrors(save.error);
  const open = (f: Faq) => setDraft({ id: f.id, body: { key: f.key, category: f.category, question: f.question, answer: f.answer, position: f.position, published: f.published, verified: f.verified, source_url: f.source_url ?? null } });
  const set = (p: Partial<FaqIn>) => setDraft((d) => (d ? { ...d, body: { ...d.body, ...p } } : d));
  return (
    <>
      <div><Btn variant="primary" onClick={() => setDraft({ id: null, body: emptyFaq() })}>{t("admin.common.newQuestion")}</Btn></div>
      {draft && (
        <Panel>
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label={t("admin.examInfo.key")} error={fe.key}><Input value={draft.body.key} onChange={(e) => set({ key: e.target.value })} /></Field>
            <Field label={t("admin.examInfo.category")} error={fe.category}><Input value={draft.body.category} onChange={(e) => set({ category: e.target.value })} /></Field>
            <Field label={t("admin.common.position")} error={fe.position}><Input type="number" value={draft.body.position ?? 0} onChange={(e) => set({ position: Number(e.target.value) })} /></Field>
          </div>
          <NamesEditor label={t("admin.common.question")} value={draft.body.question as Names} onChange={(v) => set({ question: v })} error={fe.question} />
          <NamesEditor label={t("admin.examInfo.answer")} value={draft.body.answer as Names} onChange={(v) => set({ answer: v })} error={fe.answer} />
          <Field label={t("admin.examInfo.sourceUrl")} error={fe.source_url}><Input value={draft.body.source_url ?? ""} onChange={(e) => set({ source_url: e.target.value || null })} /></Field>
          <div className="flex gap-4">
            <Check label={t("admin.common.published")} checked={draft.body.published ?? true} onChange={(v) => set({ published: v })} />
            <Check label={t("admin.examInfo.verifiedAgainstOfficialSource")} checked={draft.body.verified ?? false} onChange={(v) => set({ verified: v })} />
          </div>
          <div className="flex gap-2">
            <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate({ id: draft.id, body: { ...draft.body, question: cleanNames(draft.body.question as Names), answer: cleanNames(draft.body.answer as Names) } }, { onSuccess: () => setDraft(null) })}>{t("admin.common.save")}</Btn>
            <Btn onClick={() => setDraft(null)}>{t("admin.common.cancel")}</Btn>
          </div>
        </Panel>
      )}
      <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(f) => f.id} empty={t("admin.examInfo.noFaqYetRun")}
        cols={[
          { key: "k", head: t("admin.examInfo.key"), cell: (f) => f.key },
          { key: "c", head: t("admin.examInfo.category"), cell: (f) => en("examCategory", f.category) },
          { key: "q", head: t("admin.common.question"), cell: (f) => nm(f.question) },
          { key: "s", head: t("admin.common.status"), cell: (f) => <div className="flex gap-1">{!f.published && <Badge tone="gray">{t("admin.examInfo.hidden")}</Badge>}{f.verified ? <Badge tone="green">{t("admin.common.verified")}</Badge> : <Badge tone="gold">{t("admin.examInfo.unverified")}</Badge>}</div> },
          { key: "a", head: "", cell: (f) => <div className="flex gap-2"><Btn onClick={() => open(f)}>{t("admin.common.edit")}</Btn><Btn disabled={del.isPending} onClick={() => ask({ title: t("admin.examInfo.deleteThisQuestion"), name: nm(f.question) || f.key, danger: true, confirmLabel: t("admin.common.delete") }, () => del.mutate(f.id))}>{t("admin.common.delete")}</Btn></div> },
        ]} />
      {confirmNode}
    </>
  );
}

// --- Events ------------------------------------------------------------------------
const emptyEvent = (): EventIn => ({ exam_year: new Date().getFullYear() + 1, kind: "test", starts_on: "", ends_on: null, label: {}, verified: false, source_url: null, position: 0 });

function EventsTab() {
  const t = useT();
  const en = useEnum();
  const [ask, confirmNode] = useConfirm();
  const q = useQuery({ queryKey: EVT_KEY, queryFn: () => examInfo.events.list() });
  const [draft, setDraft] = useState<{ id: string | null; body: EventIn } | null>(null);
  const save = useAct((a: { id: string | null; body: EventIn }) => (a.id ? examInfo.events.update(a.id, a.body) : examInfo.events.create(a.body)), [EVT_KEY], t("admin.examInfo.dateSaved"));
  const del = useAct((id: string) => examInfo.events.remove(id), [EVT_KEY], t("admin.examInfo.dateDeleted"));
  const fe = fieldErrors(save.error);
  const open = (e: ExamEvent) => setDraft({ id: e.id, body: { exam_year: e.exam_year, kind: e.kind, starts_on: e.starts_on, ends_on: e.ends_on ?? null, label: e.label, verified: e.verified, source_url: e.source_url ?? null, position: e.position } });
  const set = (p: Partial<EventIn>) => setDraft((d) => (d ? { ...d, body: { ...d.body, ...p } } : d));
  return (
    <>
      <div><Btn variant="primary" onClick={() => setDraft({ id: null, body: emptyEvent() })}>{t("admin.examInfo.newDate")}</Btn></div>
      {draft && (
        <Panel>
          <div className="grid gap-3 sm:grid-cols-4">
            <Field label={t("admin.examInfo.examYear")} error={fe.exam_year}><Input type="number" value={draft.body.exam_year} onChange={(e) => set({ exam_year: Number(e.target.value) })} /></Field>
            <Field label={t("admin.common.kind")} error={fe.kind}><Select value={draft.body.kind} onChange={(e) => set({ kind: e.target.value })}>{EVENT_KINDS.map((k) => <option key={k} value={k}>{en("eventKind", k)}</option>)}</Select></Field>
            <Field label={t("admin.examInfo.starts")} error={fe.starts_on}><Input type="date" value={draft.body.starts_on} onChange={(e) => set({ starts_on: e.target.value })} /></Field>
            <Field label={t("admin.examInfo.ends")} error={fe.ends_on}><Input type="date" value={draft.body.ends_on ?? ""} onChange={(e) => set({ ends_on: e.target.value || null })} /></Field>
          </div>
          <NamesEditor label={t("admin.examInfo.label")} value={draft.body.label as Names} onChange={(v) => set({ label: v })} error={fe.label} />
          <Field label={t("admin.examInfo.sourceUrl")} error={fe.source_url}><Input value={draft.body.source_url ?? ""} onChange={(e) => set({ source_url: e.target.value || null })} /></Field>
          <Check label={t("admin.examInfo.verifiedAgainstOfficialAnnouncement")} checked={draft.body.verified ?? false} onChange={(v) => set({ verified: v })} />
          <div className="flex gap-2">
            <Btn variant="primary" disabled={save.isPending || !draft.body.starts_on} onClick={() => save.mutate({ id: draft.id, body: { ...draft.body, label: cleanNames(draft.body.label as Names) } }, { onSuccess: () => setDraft(null) })}>{t("admin.common.save")}</Btn>
            <Btn onClick={() => setDraft(null)}>{t("admin.common.cancel")}</Btn>
          </div>
        </Panel>
      )}
      <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(e) => e.id} empty={t("admin.examInfo.noDatesYetRun")}
        cols={[
          { key: "y", head: t("admin.common.year"), cell: (e) => e.exam_year },
          { key: "k", head: t("admin.common.kind"), cell: (e) => en("eventKind", e.kind) },
          { key: "l", head: t("admin.examInfo.label"), cell: (e) => nm(e.label) },
          { key: "d", head: t("admin.examInfo.dates"), cell: (e) => `${e.starts_on}${e.ends_on ? ` → ${e.ends_on}` : ""}` },
          { key: "v", head: "", cell: (e) => (e.verified ? <Badge tone="green">{t("admin.common.verified")}</Badge> : <Badge tone="gold">{t("admin.examInfo.unverified")}</Badge>) },
          { key: "a", head: "", cell: (e) => <div className="flex gap-2"><Btn onClick={() => open(e)}>{t("admin.common.edit")}</Btn><Btn disabled={del.isPending} onClick={() => ask({ title: t("admin.examInfo.deleteThisDate"), name: nm(e.label), danger: true, confirmLabel: t("admin.common.delete") }, () => del.mutate(e.id))}>{t("admin.common.delete")}</Btn></div> },
        ]} />
      {confirmNode}
    </>
  );
}

// --- Profiles & certificate rules --------------------------------------------------
function ProfilesTab() {
  const t = useT();
  const en = useEnum();
  const q = useQuery({ queryKey: PRO_KEY, queryFn: () => examInfo.profiles.list() });
  const [openId, setOpenId] = useState<string | null>(null);
  const profile = q.data?.find((p) => p.id === openId) ?? null;
  return (
    <>
      <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(p) => p.id} selected={openId} onRow={(p) => setOpenId(p.id)} empty={t("admin.examInfo.noProfilesYetRun")}
        cols={[
          { key: "d", head: t("admin.common.direction"), cell: (p) => p.direction_code ?? p.code },
          { key: "n", head: t("admin.common.name"), cell: (p) => nm(p.names) },
          { key: "s", head: t("admin.common.sections"), cell: (p) => p.sections.map((s) => nm(s.names)).join(" · ") },
          { key: "x", head: t("admin.examInfo.examDate"), cell: (p) => p.exam_date ?? "—" },
          { key: "v", head: "", cell: (p) => (p.verified ? <Badge tone="green">{t("admin.common.verified")}</Badge> : <Badge tone="gold">{t("admin.examInfo.unverified")}</Badge>) },
        ]} />
      {profile && <ProfileEditor key={profile.id} profile={profile} />}
    </>
  );
}

function ProfileEditor({ profile }: { profile: ExamProfile }) {
  const t = useT();
  const en = useEnum();
  const subjects = useSubjects();
  const [f, setF] = useState({
    exam_date: profile.exam_date ?? "",
    date_verified: profile.date_verified,
    verified: profile.verified,
    active: profile.active,
    trust_self_declared: profile.trust_self_declared,
    taper_days: profile.taper_days,
  });
  const save = useAct(() => examInfo.profiles.patch(profile.id, { ...f, exam_date: f.exam_date || null }), [PRO_KEY], t("admin.common.profileSaved"));
  const fe = fieldErrors(save.error);
  const setSubject = useAct((a: { id: string; subject: string | null }) => examInfo.profiles.setSubject(a.id, a.subject), [PRO_KEY], t("admin.examInfo.subjectLinked"));
  const rulesBySection = (id: string) => profile.certificate_rules.filter((r) => r.section_id === id);
  return (
    <Panel>
      <div className="font-extrabold">{t("admin.examInfo.ptsApp", { code: profile.direction_code ?? "", name: nm(profile.names), max: profile.max_score, app: profile.app_max_score })}</div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Field label={t("admin.examInfo.examDate")} error={fe.exam_date}><Input type="date" value={f.exam_date} onChange={(e) => setF({ ...f, exam_date: e.target.value })} /></Field>
        <Field label={t("admin.examInfo.planEndsBeforeExam")} hint={t("admin.examInfo.5To7")} error={fe.taper_days}><Input type="number" min={5} max={7} value={f.taper_days} onChange={(e) => setF({ ...f, taper_days: Number(e.target.value) })} /></Field>
      </div>
      <div className="flex flex-wrap gap-4">
        <Check label={t("admin.examInfo.dateVerified")} checked={f.date_verified} onChange={(v) => setF({ ...f, date_verified: v })} />
        <Check label={t("admin.examInfo.rulesVerified")} checked={f.verified} onChange={(v) => setF({ ...f, verified: v })} />
        <Check label={t("admin.common.active")} checked={f.active} onChange={(v) => setF({ ...f, active: v })} />
        <Check label={t("admin.examInfo.trustSelfDeclaredCertificates")} checked={f.trust_self_declared} onChange={(v) => setF({ ...f, trust_self_declared: v })} />
      </div>
      <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(undefined)}>{t("admin.examInfo.saveProfile")}</Btn>
      {profile.sections.map((s) => (
        <div key={s.id} className="space-y-2 rounded-xl border border-line p-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-extrabold">{nm(s.names)}</span>
            <Badge tone="gray">{s.role}</Badge>
            <span className="text-sm text-ink-soft">{s.question_count ? t("admin.examInfo.ptsQs", { pts: s.max_points, n: s.question_count }) : t("admin.examInfo.ptsQ", { pts: s.max_points })}</span>
            {!s.in_app && <Badge tone="gold">{t("admin.examInfo.notInApp")}</Badge>}
            {!s.exemptible && <Badge tone="gray">{t("admin.examInfo.neverExempt")}</Badge>}
            {s.role === "subject" && !s.choice_group && (
              <Select className="ml-auto" value={s.subject_id ?? ""} onChange={(e) => setSubject.mutate({ id: s.id, subject: e.target.value || null })}>
                <option value="">{t("admin.examInfo.catalogSubjectNone")}</option>
                {(subjects.data ?? []).map((x) => <option key={x.id} value={x.id}>{nm(x.names)}</option>)}
              </Select>
            )}
          </div>
          {s.exemptible && <RuleList section={s.id} rules={rulesBySection(s.id)} />}
        </div>
      ))}
    </Panel>
  );
}

function RuleList({ section, rules }: { section: string; rules: CertRule[] }) {
  const t = useT();
  const en = useEnum();
  const [adding, setAdding] = useState(false);
  const add = useAct((cert_type: string) => examInfo.rules.create({ section_id: section, cert_type, active: false, awarded_fraction: 1, verified: false }), [PRO_KEY], t("admin.examInfo.ruleAdded"));
  const [type, setType] = useState("ielts");
  return (
    <div className="space-y-1">
      {rules.map((r) => <RuleRow key={r.id} rule={r} />)}
      {adding ? (
        <div className="flex gap-2">
          <Select value={type} onChange={(e) => setType(e.target.value)}>{CERT_TYPES.map((c) => <option key={c} value={c}>{c}</option>)}</Select>
          <Btn variant="primary" disabled={add.isPending} onClick={() => add.mutate(type, { onSuccess: () => setAdding(false) })}>{t("admin.examInfo.addInactiveRule")}</Btn>
          <Btn onClick={() => setAdding(false)}>{t("admin.common.cancel")}</Btn>
        </div>
      ) : <Btn onClick={() => setAdding(true)}>{t("admin.examInfo.addCertificateRule")}</Btn>}
    </div>
  );
}

function RuleRow({ rule }: { rule: CertRule }) {
  const t = useT();
  const en = useEnum();
  const [r, setR] = useState({ level_label: rule.level_label ?? "", min_value: rule.min_value == null ? "" : String(rule.min_value), awarded_fraction: String(rule.awarded_fraction), verified: rule.verified, active: rule.active });
  const save = useAct(() => examInfo.rules.update(rule.id, {
    cert_type: rule.cert_type, language_subject_id: rule.language_subject_id, note: rule.note, source_url: rule.source_url,
    level_label: r.level_label || null, min_value: r.min_value === "" ? null : r.min_value, awarded_fraction: r.awarded_fraction, verified: r.verified, active: r.active,
  } as never), [PRO_KEY], t("admin.examInfo.ruleSaved"));
  const fe = fieldErrors(save.error);
  const del = useAct(() => examInfo.rules.remove(rule.id), [PRO_KEY], t("admin.examInfo.ruleDeleted"));
  const [ask, confirmNode] = useConfirm();
  return (
    <><div className="flex flex-wrap items-end gap-2">
      <Badge tone="blue">{rule.cert_type}</Badge>
      <Field label={t("admin.examInfo.label")} error={fe.level_label}><Input value={r.level_label} onChange={(e) => setR({ ...r, level_label: e.target.value })} /></Field>
      <Field label={t("admin.examInfo.minValue")} error={fe.min_value}><Input className="w-24" value={r.min_value} onChange={(e) => setR({ ...r, min_value: e.target.value })} /></Field>
      <Field label={t("admin.examInfo.fraction")} error={fe.awarded_fraction}><Input className="w-20" value={r.awarded_fraction} onChange={(e) => setR({ ...r, awarded_fraction: e.target.value })} /></Field>
      <Check label={t("admin.common.verified")} checked={r.verified} onChange={(v) => setR({ ...r, verified: v })} />
      <Check label={t("admin.common.active")} checked={r.active} onChange={(v) => setR({ ...r, active: v })} />
      <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(undefined)}>{t("admin.common.save")}</Btn>
      <Btn disabled={del.isPending} onClick={() => ask({ title: t("admin.examInfo.deleteThisRule"), name: `${rule.cert_type} · ${rule.level_label}`, danger: true, confirmLabel: t("admin.common.delete") }, () => del.mutate(undefined))}>{t("admin.common.delete")}</Btn>
    </div>
    {confirmNode}
    </>
  );
}
