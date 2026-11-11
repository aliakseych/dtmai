"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useAct, useSubjects } from "@/lib/catalog";
import { examInfo, type CertRule, type EventIn, type ExamEvent, type ExamProfile, type Faq, type FaqIn } from "@/lib/examInfo";
import { nm, type Names } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader, Select, Tabs } from "@/components/ui/controls";
import { cleanNames, NamesEditor } from "@/components/ui/names";
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
  const [tab, setTab] = useState<Tab>("faq");
  return (
    <>
      <PageHeader title="Exam info" sub="Exam rules, dates, FAQ and certificate exemptions shown to learners. Seeded once; your edits are never overwritten." />
      <Tabs value={tab} onChange={setTab} items={[{ id: "faq", label: "FAQ" }, { id: "events", label: "Dates" }, { id: "profiles", label: "Directions & certificates" }]} />
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
  const q = useQuery({ queryKey: FAQ_KEY, queryFn: () => examInfo.faq.list() });
  const [draft, setDraft] = useState<{ id: string | null; body: FaqIn } | null>(null);
  const save = useAct((a: { id: string | null; body: FaqIn }) => (a.id ? examInfo.faq.update(a.id, a.body) : examInfo.faq.create(a.body)), [FAQ_KEY], "FAQ saved");
  const del = useAct((id: string) => examInfo.faq.remove(id), [FAQ_KEY], "FAQ deleted");
  const open = (f: Faq) => setDraft({ id: f.id, body: { key: f.key, category: f.category, question: f.question, answer: f.answer, position: f.position, published: f.published, verified: f.verified, source_url: f.source_url ?? null } });
  const set = (p: Partial<FaqIn>) => setDraft((d) => (d ? { ...d, body: { ...d.body, ...p } } : d));
  return (
    <>
      <div><Btn variant="primary" onClick={() => setDraft({ id: null, body: emptyFaq() })}>New question</Btn></div>
      {draft && (
        <Panel>
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label="Key"><Input value={draft.body.key} onChange={(e) => set({ key: e.target.value })} /></Field>
            <Field label="Category"><Input value={draft.body.category} onChange={(e) => set({ category: e.target.value })} /></Field>
            <Field label="Position"><Input type="number" value={draft.body.position ?? 0} onChange={(e) => set({ position: Number(e.target.value) })} /></Field>
          </div>
          <NamesEditor label="Question" value={draft.body.question as Names} onChange={(v) => set({ question: v })} />
          <NamesEditor label="Answer" value={draft.body.answer as Names} onChange={(v) => set({ answer: v })} />
          <Field label="Source URL"><Input value={draft.body.source_url ?? ""} onChange={(e) => set({ source_url: e.target.value || null })} /></Field>
          <div className="flex gap-4">
            <Check label="Published" checked={draft.body.published ?? true} onChange={(v) => set({ published: v })} />
            <Check label="Verified against official source" checked={draft.body.verified ?? false} onChange={(v) => set({ verified: v })} />
          </div>
          <div className="flex gap-2">
            <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate({ id: draft.id, body: { ...draft.body, question: cleanNames(draft.body.question as Names), answer: cleanNames(draft.body.answer as Names) } }, { onSuccess: () => setDraft(null) })}>Save</Btn>
            <Btn onClick={() => setDraft(null)}>Cancel</Btn>
          </div>
        </Panel>
      )}
      <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(f) => f.id} empty="No FAQ yet. Run the seed command."
        cols={[
          { key: "k", head: "Key", cell: (f) => f.key },
          { key: "c", head: "Category", cell: (f) => f.category },
          { key: "q", head: "Question", cell: (f) => nm(f.question) },
          { key: "s", head: "Status", cell: (f) => <div className="flex gap-1">{!f.published && <Badge tone="gray">Hidden</Badge>}{f.verified ? <Badge tone="green">Verified</Badge> : <Badge tone="gold">Unverified</Badge>}</div> },
          { key: "a", head: "", cell: (f) => <div className="flex gap-2"><Btn onClick={() => open(f)}>Edit</Btn><Btn disabled={del.isPending} onClick={() => confirm("Delete this question?") && del.mutate(f.id)}>Delete</Btn></div> },
        ]} />
    </>
  );
}

// --- Events ------------------------------------------------------------------------
const emptyEvent = (): EventIn => ({ exam_year: new Date().getFullYear() + 1, kind: "test", starts_on: "", ends_on: null, label: {}, verified: false, source_url: null, position: 0 });

function EventsTab() {
  const q = useQuery({ queryKey: EVT_KEY, queryFn: () => examInfo.events.list() });
  const [draft, setDraft] = useState<{ id: string | null; body: EventIn } | null>(null);
  const save = useAct((a: { id: string | null; body: EventIn }) => (a.id ? examInfo.events.update(a.id, a.body) : examInfo.events.create(a.body)), [EVT_KEY], "Date saved");
  const del = useAct((id: string) => examInfo.events.remove(id), [EVT_KEY], "Date deleted");
  const open = (e: ExamEvent) => setDraft({ id: e.id, body: { exam_year: e.exam_year, kind: e.kind, starts_on: e.starts_on, ends_on: e.ends_on ?? null, label: e.label, verified: e.verified, source_url: e.source_url ?? null, position: e.position } });
  const set = (p: Partial<EventIn>) => setDraft((d) => (d ? { ...d, body: { ...d.body, ...p } } : d));
  return (
    <>
      <div><Btn variant="primary" onClick={() => setDraft({ id: null, body: emptyEvent() })}>New date</Btn></div>
      {draft && (
        <Panel>
          <div className="grid gap-3 sm:grid-cols-4">
            <Field label="Exam year"><Input type="number" value={draft.body.exam_year} onChange={(e) => set({ exam_year: Number(e.target.value) })} /></Field>
            <Field label="Kind"><Select value={draft.body.kind} onChange={(e) => set({ kind: e.target.value })}>{EVENT_KINDS.map((k) => <option key={k} value={k}>{k}</option>)}</Select></Field>
            <Field label="Starts"><Input type="date" value={draft.body.starts_on} onChange={(e) => set({ starts_on: e.target.value })} /></Field>
            <Field label="Ends"><Input type="date" value={draft.body.ends_on ?? ""} onChange={(e) => set({ ends_on: e.target.value || null })} /></Field>
          </div>
          <NamesEditor label="Label" value={draft.body.label as Names} onChange={(v) => set({ label: v })} />
          <Field label="Source URL"><Input value={draft.body.source_url ?? ""} onChange={(e) => set({ source_url: e.target.value || null })} /></Field>
          <Check label="Verified against official announcement" checked={draft.body.verified ?? false} onChange={(v) => set({ verified: v })} />
          <div className="flex gap-2">
            <Btn variant="primary" disabled={save.isPending || !draft.body.starts_on} onClick={() => save.mutate({ id: draft.id, body: { ...draft.body, label: cleanNames(draft.body.label as Names) } }, { onSuccess: () => setDraft(null) })}>Save</Btn>
            <Btn onClick={() => setDraft(null)}>Cancel</Btn>
          </div>
        </Panel>
      )}
      <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(e) => e.id} empty="No dates yet. Run the seed command."
        cols={[
          { key: "y", head: "Year", cell: (e) => e.exam_year },
          { key: "k", head: "Kind", cell: (e) => e.kind },
          { key: "l", head: "Label", cell: (e) => nm(e.label) },
          { key: "d", head: "Dates", cell: (e) => `${e.starts_on}${e.ends_on ? ` → ${e.ends_on}` : ""}` },
          { key: "v", head: "", cell: (e) => (e.verified ? <Badge tone="green">Verified</Badge> : <Badge tone="gold">Unverified</Badge>) },
          { key: "a", head: "", cell: (e) => <div className="flex gap-2"><Btn onClick={() => open(e)}>Edit</Btn><Btn disabled={del.isPending} onClick={() => confirm("Delete this date?") && del.mutate(e.id)}>Delete</Btn></div> },
        ]} />
    </>
  );
}

// --- Profiles & certificate rules --------------------------------------------------
function ProfilesTab() {
  const q = useQuery({ queryKey: PRO_KEY, queryFn: () => examInfo.profiles.list() });
  const [openId, setOpenId] = useState<string | null>(null);
  const profile = q.data?.find((p) => p.id === openId) ?? null;
  return (
    <>
      <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(p) => p.id} selected={openId} onRow={(p) => setOpenId(p.id)} empty="No profiles yet. Run the seed command."
        cols={[
          { key: "d", head: "Direction", cell: (p) => p.direction_code ?? p.code },
          { key: "n", head: "Name", cell: (p) => nm(p.names) },
          { key: "s", head: "Sections", cell: (p) => p.sections.map((s) => nm(s.names)).join(" · ") },
          { key: "x", head: "Exam date", cell: (p) => p.exam_date ?? "—" },
          { key: "v", head: "", cell: (p) => (p.verified ? <Badge tone="green">Verified</Badge> : <Badge tone="gold">Unverified</Badge>) },
        ]} />
      {profile && <ProfileEditor key={profile.id} profile={profile} />}
    </>
  );
}

function ProfileEditor({ profile }: { profile: ExamProfile }) {
  const subjects = useSubjects();
  const [f, setF] = useState({
    exam_date: profile.exam_date ?? "",
    date_verified: profile.date_verified,
    verified: profile.verified,
    active: profile.active,
    trust_self_declared: profile.trust_self_declared,
    taper_days: profile.taper_days,
  });
  const save = useAct(() => examInfo.profiles.patch(profile.id, { ...f, exam_date: f.exam_date || null }), [PRO_KEY], "Profile saved");
  const setSubject = useAct((a: { id: string; subject: string | null }) => examInfo.profiles.setSubject(a.id, a.subject), [PRO_KEY], "Subject linked");
  const rulesBySection = (id: string) => profile.certificate_rules.filter((r) => r.section_id === id);
  return (
    <Panel>
      <div className="font-extrabold">{profile.direction_code} · {nm(profile.names)} · {profile.max_score} pts (in app: {profile.app_max_score})</div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Field label="Exam date"><Input type="date" value={f.exam_date} onChange={(e) => setF({ ...f, exam_date: e.target.value })} /></Field>
        <Field label="Plan ends before exam (days)" hint="5 to 7"><Input type="number" min={5} max={7} value={f.taper_days} onChange={(e) => setF({ ...f, taper_days: Number(e.target.value) })} /></Field>
      </div>
      <div className="flex flex-wrap gap-4">
        <Check label="Date verified" checked={f.date_verified} onChange={(v) => setF({ ...f, date_verified: v })} />
        <Check label="Rules verified" checked={f.verified} onChange={(v) => setF({ ...f, verified: v })} />
        <Check label="Active" checked={f.active} onChange={(v) => setF({ ...f, active: v })} />
        <Check label="Trust self-declared certificates" checked={f.trust_self_declared} onChange={(v) => setF({ ...f, trust_self_declared: v })} />
      </div>
      <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(undefined)}>Save profile</Btn>
      {profile.sections.map((s) => (
        <div key={s.id} className="space-y-2 rounded-lg border border-line p-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-extrabold">{nm(s.names)}</span>
            <Badge tone="gray">{s.role}</Badge>
            <span className="text-sm text-ink-soft">{s.max_points} pts{s.question_count ? ` · ${s.question_count} questions` : ""}</span>
            {!s.in_app && <Badge tone="gold">Not in app</Badge>}
            {!s.exemptible && <Badge tone="gray">Never exempt</Badge>}
            {s.role === "subject" && !s.choice_group && (
              <Select className="ml-auto" value={s.subject_id ?? ""} onChange={(e) => setSubject.mutate({ id: s.id, subject: e.target.value || null })}>
                <option value="">Catalog subject: none</option>
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
  const [adding, setAdding] = useState(false);
  const add = useAct((cert_type: string) => examInfo.rules.create({ section_id: section, cert_type, active: false, awarded_fraction: 1, verified: false }), [PRO_KEY], "Rule added");
  const [type, setType] = useState("ielts");
  return (
    <div className="space-y-1">
      {rules.map((r) => <RuleRow key={r.id} rule={r} />)}
      {adding ? (
        <div className="flex gap-2">
          <Select value={type} onChange={(e) => setType(e.target.value)}>{CERT_TYPES.map((c) => <option key={c} value={c}>{c}</option>)}</Select>
          <Btn variant="primary" disabled={add.isPending} onClick={() => add.mutate(type, { onSuccess: () => setAdding(false) })}>Add inactive rule</Btn>
          <Btn onClick={() => setAdding(false)}>Cancel</Btn>
        </div>
      ) : <Btn onClick={() => setAdding(true)}>Add certificate rule</Btn>}
    </div>
  );
}

function RuleRow({ rule }: { rule: CertRule }) {
  const [r, setR] = useState({ level_label: rule.level_label ?? "", min_value: rule.min_value == null ? "" : String(rule.min_value), awarded_fraction: String(rule.awarded_fraction), verified: rule.verified, active: rule.active });
  const save = useAct(() => examInfo.rules.update(rule.id, {
    cert_type: rule.cert_type, language_subject_id: rule.language_subject_id, note: rule.note, source_url: rule.source_url,
    level_label: r.level_label || null, min_value: r.min_value === "" ? null : r.min_value, awarded_fraction: r.awarded_fraction, verified: r.verified, active: r.active,
  } as never), [PRO_KEY], "Rule saved");
  const del = useAct(() => examInfo.rules.remove(rule.id), [PRO_KEY], "Rule deleted");
  return (
    <div className="flex flex-wrap items-end gap-2">
      <Badge tone="blue">{rule.cert_type}</Badge>
      <Field label="Label"><Input value={r.level_label} onChange={(e) => setR({ ...r, level_label: e.target.value })} /></Field>
      <Field label="Min value"><Input className="w-24" value={r.min_value} onChange={(e) => setR({ ...r, min_value: e.target.value })} /></Field>
      <Field label="Fraction"><Input className="w-20" value={r.awarded_fraction} onChange={(e) => setR({ ...r, awarded_fraction: e.target.value })} /></Field>
      <Check label="Verified" checked={r.verified} onChange={(v) => setR({ ...r, verified: v })} />
      <Check label="Active" checked={r.active} onChange={(v) => setR({ ...r, active: v })} />
      <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(undefined)}>Save</Btn>
      <Btn disabled={del.isPending} onClick={() => confirm("Delete this rule?") && del.mutate(undefined)}>Delete</Btn>
    </div>
  );
}
