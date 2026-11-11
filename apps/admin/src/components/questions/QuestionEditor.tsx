"use client";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useToast } from "@dtmai/ui";
import { qk, useAct, useBases, useSubjects, useTopics, useTypes, type Question } from "@/lib/catalog";
import { bank, draftFrom, draftTo, emptyDraft, validateDraft, type Draft, type Status } from "@/lib/questions";
import { uploadMedia } from "@/lib/media";
import { mediaUrl } from "@/lib/env";
import { LOCALE_LIST, QUESTION_KINDS, QUESTION_STATUSES, errMsg, nm, type Kind } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, Select, StatusBadge, Tabs, Textarea } from "@/components/ui/controls";
import { Drawer } from "@/components/ui/overlay";
import { Md } from "@/components/ui/markdown";
import { LangInput } from "@/components/ui/lang";
import { KindEditor } from "./KindEditor";

interface Form {
  kind: Kind; subject_id: string; topic_id: string; type_id: string; language: string; stem: string; difficulty: number;
  source_id: string; passage_id: string; answer_official: boolean; media: { type: "image"; key: string }[]; draft: Draft;
}
const blank = (p: Partial<Form> = {}): Form => ({ kind: "single_choice", subject_id: "", topic_id: "", type_id: "", language: "uz-Latn", stem: "", difficulty: 1000, source_id: "", passage_id: "", answer_official: false, media: [], draft: emptyDraft("single_choice"), ...p });
const fromQ = (q: Question): Form => ({
  kind: q.kind as Kind, subject_id: q.subject_id, topic_id: q.topic_id, type_id: q.type_id, language: q.language, stem: q.stem, difficulty: q.difficulty,
  source_id: q.source_id ?? "", passage_id: q.passage_id ?? "", answer_official: q.answer_official,
  media: (q.media as { type?: string; key?: string }[]).filter((m) => m.key).map((m) => ({ type: "image", key: m.key! })),
  draft: draftFrom(q.kind as Kind, q.payload, q.answer),
});

export function QuestionEditor({ id, preset, onClose }: { id: string | null | "new"; preset?: Partial<Form>; onClose: () => void }) {
  const open = id !== null;
  const isNew = id === "new";
  const toast = useToast();
  const [f, setF] = useState<Form>(blank());
  const [tab, setTab] = useState<"edit" | "explain" | "status">("edit");
  const q = useQuery({ queryKey: ["question", id], queryFn: () => bank.get(id as string), enabled: open && !isNew });
  useEffect(() => { if (isNew) { setF(blank(preset)); setTab("edit"); } }, [isNew, id]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (q.data) setF(fromQ(q.data)); }, [q.data]);
  const subjects = useSubjects(), types = useTypes(), bases = useBases(), topics = useTopics(f.subject_id || undefined);
  const passages = useQuery({ queryKey: ["passages"], queryFn: bank.passages, enabled: open });
  const set = (p: Partial<Form>) => setF((x) => ({ ...x, ...p }));
  const inv = [["questions"], ["question", id]];
  const save = useAct(async () => {
    const err = validateDraft(f.draft) ?? (!f.stem.trim() ? "Stem is required" : !f.subject_id || !f.topic_id || !f.type_id ? "Subject, topic and type are required" : null);
    if (err) throw new Error(err);
    const { payload, answer } = draftTo(f.draft);
    const common = { language: f.language, stem: f.stem, difficulty: f.difficulty, source_id: f.source_id || null, passage_id: f.passage_id || null, topic_id: f.topic_id, type_id: f.type_id, media: f.media, payload, answer };
    if (isNew) return bank.create({ ...common, kind: f.kind, subject_id: f.subject_id, answer_official: f.answer_official, status: "draft" });
    return bank.patch(id as string, common);
  }, inv, "Saved");
  const typeOptions = (types.data ?? []).filter((t) => t.kind === f.kind);
  const addImage = async (file?: File) => { if (!file) return; try { const { key } = await uploadMedia(file); set({ media: [...f.media, { type: "image", key }] }); } catch (e) { toast(errMsg(e), "error"); } };
  const [key, setKey] = useState("");

  return (
    <Drawer open={open} onClose={onClose} width="max-w-5xl" title={<span className="flex items-center gap-2">{isNew ? "New question" : "Question"} {q.data && <StatusBadge status={q.data.status} />}{q.data && q.data.report_count > 0 && <Badge tone="red">{q.data.report_count} reports</Badge>}</span>}
      footer={<><Btn onClick={onClose}>Close</Btn><Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(undefined, { onSuccess: (r) => isNew && (r as Question).id ? onClose() : undefined })}>{isNew ? "Create draft" : "Save"}</Btn></>}>
      {!isNew && <Tabs value={tab} onChange={setTab} items={[{ id: "edit", label: "Content" }, { id: "explain", label: "Explanations" }, { id: "status", label: "Status & stats" }]} />}
      {tab === "edit" && (
        <div className="mt-3 grid grid-cols-[1fr_20rem] gap-4">
          <div className="space-y-3">
            <Field label="Stem (Markdown + $LaTeX$)"><Textarea rows={6} value={f.stem} onChange={(e) => set({ stem: e.target.value })} /></Field>
            <div className="rounded border border-line bg-snow p-2"><div className="mb-1 text-[10px] font-extrabold uppercase text-ink-soft">Preview</div><Md text={f.stem || "…"} />
              {f.media.map((m) => <img key={m.key} alt="" src={mediaUrl(m.key)} className="mt-2 max-h-48 rounded" />)}</div>
            <KindEditor d={f.draft} onChange={(draft) => set({ draft })} />
          </div>
          <div className="space-y-3">
            <Field label="Kind" hint={isNew ? undefined : "Fixed after creation"}>
              <Select disabled={!isNew} value={f.kind} onChange={(e) => set({ kind: e.target.value as Kind, type_id: "", draft: emptyDraft(e.target.value as Kind) })}>{QUESTION_KINDS.map((k) => <option key={k}>{k}</option>)}</Select></Field>
            <Field label="Subject"><Select disabled={!isNew} value={f.subject_id} onChange={(e) => set({ subject_id: e.target.value, topic_id: "" })}><option value="">—</option>{subjects.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select></Field>
            <Field label="Topic"><Select value={f.topic_id} onChange={(e) => set({ topic_id: e.target.value })}><option value="">—</option>{topics.data?.map((t) => <option key={t.id} value={t.id}>{nm(t.names)}</option>)}</Select></Field>
            <Field label="Type" hint={`Types of kind ${f.kind}`}><Select value={f.type_id} onChange={(e) => set({ type_id: e.target.value })}><option value="">—</option>{typeOptions.map((t) => <option key={t.id} value={t.id}>{nm(t.names)}</option>)}</Select></Field>
            <div className="grid grid-cols-2 gap-2">
              <Field label="Language"><LangInput value={f.language} onChange={(language) => set({ language })} /></Field>
              <Field label="Difficulty (ELO)"><Input type="number" value={f.difficulty} onChange={(e) => set({ difficulty: Number(e.target.value) })} /></Field>
            </div>
            <Field label="Source"><Select value={f.source_id} onChange={(e) => set({ source_id: e.target.value })}><option value="">—</option>{bases.data?.map((b) => <option key={b.id} value={b.id}>{nm(b.names)}</option>)}</Select></Field>
            <Field label="Passage"><Select value={f.passage_id} onChange={(e) => set({ passage_id: e.target.value })}><option value="">—</option>{passages.data?.map((p) => <option key={p.id} value={p.id}>{p.title || p.id.slice(0, 8)}</option>)}</Select></Field>
            {isNew && <Check checked={f.answer_official} onChange={(answer_official) => set({ answer_official })} label="Answer is from the official key" />}
            <div className="space-y-1.5"><h4 className="text-xs font-extrabold uppercase text-ink-soft">Images</h4>
              {f.media.map((m, i) => <div key={m.key} className="flex items-center gap-2"><img alt="" src={mediaUrl(m.key)} className="h-10 rounded border border-line" /><code className="min-w-0 flex-1 truncate text-xs">{m.key}</code><Btn variant="ghost" onClick={() => set({ media: f.media.filter((_, j) => j !== i) })}>×</Btn></div>)}
              <label className="inline-block cursor-pointer rounded border border-line px-2 py-1 text-sm hover:bg-snow">Upload image<input type="file" accept="image/*" hidden onChange={(e) => addImage(e.target.files?.[0])} /></label>
              <div className="flex gap-1"><Input placeholder="…or paste a storage key" value={key} onChange={(e) => setKey(e.target.value)} /><Btn disabled={!key.trim()} onClick={() => { set({ media: [...f.media, { type: "image", key: key.trim() }] }); setKey(""); }}>Add</Btn></div>
            </div>
          </div>
        </div>
      )}
      {tab === "explain" && !isNew && <Explanations id={id as string} />}
      {tab === "status" && q.data && <StatusPanel q={q.data} />}
    </Drawer>
  );
}

function Explanations({ id }: { id: string }) {
  const [locale, setLocale] = useState(LOCALE_LIST[0]);
  const [text, setText] = useState("");
  const e = useQuery({ queryKey: ["expl", id, locale], queryFn: () => bank.explanation(id, locale) });
  useEffect(() => setText(e.data?.text ?? ""), [e.data]);
  const save = useAct(() => bank.putExplanation(id, locale, text), [["expl", id, locale]], "Explanation saved");
  return (
    <div className="mt-3 space-y-2">
      <Tabs value={locale} onChange={setLocale} items={LOCALE_LIST.map((l) => ({ id: l, label: l }))} />
      <div className="grid grid-cols-2 gap-3">
        <Textarea rows={12} value={text} onChange={(x) => setText(x.target.value)} placeholder="Explanation (Markdown + $LaTeX$)" />
        <div className="rounded border border-line bg-snow p-2"><Md text={text || "…"} /></div>
      </div>
      <Btn variant="primary" disabled={!text.trim() || save.isPending} onClick={() => save.mutate()}>Save {locale}</Btn>
    </div>
  );
}

function StatusPanel({ q }: { q: Question }) {
  const [status, setStatus] = useState<Status>(q.status as Status);
  const [reason, setReason] = useState("");
  const act = useAct(() => bank.setStatus(q.id, status, reason), [["questions"], ["question", q.id]], "Status changed");
  return (
    <div className="mt-3 max-w-lg space-y-3">
      <div className="grid grid-cols-4 gap-2 text-center text-sm">
        <Stat k="Attempts" v={q.attempts} /><Stat k="Correct" v={q.correct_rate == null ? "—" : `${Math.round(q.correct_rate * 100)}%`} /><Stat k="Reports" v={q.report_count} /><Stat k="Official key" v={q.answer_official ? "yes" : "no"} />
      </div>
      <Field label="New status"><Select value={status} onChange={(e) => setStatus(e.target.value as Status)}>{QUESTION_STATUSES.map((s) => <option key={s}>{s}</option>)}</Select></Field>
      <Field label="Reason (audited)"><Input value={reason} onChange={(e) => setReason(e.target.value)} /></Field>
      <Btn variant="primary" disabled={status === q.status || act.isPending} onClick={() => act.mutate()}>Change status</Btn>
    </div>
  );
}
const Stat = ({ k, v }: { k: string; v: React.ReactNode }) => <div className="rounded border border-line p-2"><div className="text-[10px] uppercase text-ink-soft">{k}</div><div className="font-extrabold">{v}</div></div>;
