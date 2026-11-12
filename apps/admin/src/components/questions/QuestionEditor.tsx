"use client";
import { useT } from "@/lib/i18n";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Icon, useToast } from "@dtmai/ui";
import { qk, useAct, useBases, useSubjects, useTopics, useTypes, type Question } from "@/lib/catalog";
import { bank, draftFrom, draftTo, emptyDraft, validateDraft, type Draft, type Status } from "@/lib/questions";
import { uploadMedia } from "@/lib/media";
import { mediaUrl } from "@/lib/env";
import { LOCALE_LIST, QUESTION_KINDS, QUESTION_STATUSES, errMsg, fieldErrors, nm, type Kind } from "@/lib/util";
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
  const t = useT();
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
  const set = (p: Partial<Form>) => { setTouched(true); setF((x) => ({ ...x, ...p })); };
  const inv = [["questions"], ["question", id]];
  const save = useAct(async () => {
    const err = validateDraft(f.draft) ?? (!f.stem.trim() ? "admin.validate.stemRequired" : !f.subject_id || !f.topic_id || !f.type_id ? "admin.validate.subjectTopicType" : null);
    if (err) throw new Error(t(err));
    const { payload, answer } = draftTo(f.draft);
    const common = { language: f.language, stem: f.stem, difficulty: f.difficulty, source_id: f.source_id || null, passage_id: f.passage_id || null, topic_id: f.topic_id, type_id: f.type_id, media: f.media, payload, answer };
    if (isNew) return bank.create({ ...common, kind: f.kind, subject_id: f.subject_id, answer_official: f.answer_official, status: "draft" });
    return bank.patch(id as string, common);
  }, inv, t("admin.common.saved"));
  const [touched, setTouched] = useState(false);
  useEffect(() => { setTouched(false); }, [id]);
  const draftErr = validateDraft(f.draft);
  const req = (ok: boolean) => (ok ? undefined : t("admin.common.required"));
  const ce = { stem: req(!!f.stem.trim()), subject_id: req(!!f.subject_id), topic_id: req(!!f.topic_id), type_id: req(!!f.type_id) };
  const valid = !draftErr && !ce.stem && !ce.subject_id && !ce.topic_id && !ce.type_id;
  const se = fieldErrors(save.error);
  const fe = (k: keyof typeof ce) => (touched ? ce[k] : undefined) ?? se[k];
  const typeOptions = (types.data ?? []).filter((t) => t.kind === f.kind);
  const addImage = async (file?: File) => { if (!file) return; try { const { key } = await uploadMedia(file); set({ media: [...f.media, { type: "image", key }] }); } catch (e) { toast(errMsg(e), "error"); } };
  const [key, setKey] = useState("");

  return (
    <Drawer open={open} onClose={onClose} width="max-w-5xl" title={<span className="flex items-center gap-2">{isNew ? t("admin.common.newQuestion") : t("admin.common.question")} {q.data && <StatusBadge status={q.data.status} />}{q.data && q.data.report_count > 0 && <Badge tone="red">{t("admin.questions.reportsN", { n: q.data.report_count })}</Badge>}</span>}
      footer={<><Btn onClick={onClose}>{t("admin.common.close")}</Btn><Btn variant="primary" disabled={save.isPending || !valid} onClick={() => save.mutate(undefined, { onSuccess: (r) => isNew && (r as Question).id ? onClose() : undefined })}>{isNew ? t("admin.questions.createDraft") : t("admin.common.save")}</Btn></>}>
      {!isNew && <Tabs value={tab} onChange={setTab} items={[{ id: "edit", label: t("admin.questions.content") }, { id: "explain", label: t("admin.questions.explanations") }, { id: "status", label: t("admin.questions.statusStats") }]} />}
      {tab === "edit" && (
        <div className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-[1fr_20rem]">
          <div className="space-y-3">
            <Field label={t("admin.questions.stemMarkdownLatex")} error={fe("stem")}><Textarea rows={6} value={f.stem} onChange={(e) => set({ stem: e.target.value })} /></Field>
            <div className="rounded-xl border border-line bg-snow p-2"><div className="mb-1 text-xs font-extrabold uppercase text-ink-soft">{t("admin.common.preview")}</div><Md text={f.stem || "…"} />
              {f.media.map((m) => <img key={m.key} alt="" src={mediaUrl(m.key)} className="mt-2 max-h-48 rounded" />)}</div>
            <KindEditor d={f.draft} onChange={(draft) => set({ draft })} />
            {(touched && draftErr ? t(draftErr) : se.payload ?? se.answer) && <p role="alert" className="text-xs font-bold text-red-deep">{touched && draftErr ? t(draftErr) : se.payload ?? se.answer}</p>}
          </div>
          <div className="space-y-3">
            <Field label={t("admin.common.kind")} hint={isNew ? undefined : t("admin.questions.fixedAfterCreation")}>
              <Select disabled={!isNew} value={f.kind} onChange={(e) => set({ kind: e.target.value as Kind, type_id: "", draft: emptyDraft(e.target.value as Kind) })}>{QUESTION_KINDS.map((k) => <option key={k}>{k}</option>)}</Select></Field>
            <Field label={t("admin.common.subject")} error={fe("subject_id")}><Select disabled={!isNew} value={f.subject_id} onChange={(e) => set({ subject_id: e.target.value, topic_id: "" })}><option value="">—</option>{subjects.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select></Field>
            <Field label={t("admin.common.topic")} error={fe("topic_id")}><Select value={f.topic_id} onChange={(e) => set({ topic_id: e.target.value })}><option value="">—</option>{topics.data?.map((t) => <option key={t.id} value={t.id}>{nm(t.names)}</option>)}</Select></Field>
            <Field label={t("admin.common.type")} hint={t("admin.questions.typesOfKind", { kind: f.kind })} error={fe("type_id")}><Select value={f.type_id} onChange={(e) => set({ type_id: e.target.value })}><option value="">—</option>{typeOptions.map((t) => <option key={t.id} value={t.id}>{nm(t.names)}</option>)}</Select></Field>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              <Field label={t("admin.common.language")} error={se.language}><LangInput value={f.language} onChange={(language) => set({ language })} /></Field>
              <Field label={t("admin.questions.difficultyElo")} error={se.difficulty}><Input type="number" value={f.difficulty} onChange={(e) => set({ difficulty: Number(e.target.value) })} /></Field>
            </div>
            <Field label={t("admin.common.source")}><Select value={f.source_id} onChange={(e) => set({ source_id: e.target.value })}><option value="">—</option>{bases.data?.map((b) => <option key={b.id} value={b.id}>{nm(b.names)}</option>)}</Select></Field>
            <Field label={t("admin.questions.passage")}><Select value={f.passage_id} onChange={(e) => set({ passage_id: e.target.value })}><option value="">—</option>{passages.data?.map((p) => <option key={p.id} value={p.id}>{p.title || p.id.slice(0, 8)}</option>)}</Select></Field>
            {isNew && <Check checked={f.answer_official} onChange={(answer_official) => set({ answer_official })} label={t("admin.questions.answerIsFromThe")} />}
            <div className="space-y-1.5"><h4 className="text-xs font-extrabold uppercase text-ink-soft">{t("admin.questions.images")}</h4>
              {f.media.map((m, i) => <div key={m.key} className="flex items-center gap-2"><img alt="" src={mediaUrl(m.key)} className="h-10 rounded-lg border border-line" /><code className="min-w-0 flex-1 truncate text-xs">{m.key}</code><Btn variant="ghost" aria-label={t("admin.common.remove")} onClick={() => set({ media: f.media.filter((_, j) => j !== i) })}><Icon name="close" size={16} /></Btn></div>)}
              <label className="inline-block cursor-pointer rounded border border-line px-2 py-1 text-sm hover:bg-snow">{t("admin.questions.uploadImage")}<input type="file" accept="image/png,image/jpeg,image/webp,image/gif" hidden onChange={(e) => addImage(e.target.files?.[0])} /></label>
              <div className="flex gap-1"><Input placeholder={t("admin.questions.orPasteAStorage")} value={key} onChange={(e) => setKey(e.target.value)} /><Btn disabled={!key.trim()} onClick={() => { set({ media: [...f.media, { type: "image", key: key.trim() }] }); setKey(""); }}>{t("admin.questions.add")}</Btn></div>
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
  const t = useT();
  const [locale, setLocale] = useState(LOCALE_LIST[0]);
  const [text, setText] = useState("");
  const e = useQuery({ queryKey: ["expl", id, locale], queryFn: () => bank.explanation(id, locale) });
  useEffect(() => setText(e.data?.text ?? ""), [e.data]);
  const save = useAct(() => bank.putExplanation(id, locale, text), [["expl", id, locale]], t("admin.questions.explanationSaved"));
  return (
    <div className="mt-3 space-y-2">
      <Tabs value={locale} onChange={setLocale} items={LOCALE_LIST.map((l) => ({ id: l, label: l }))} />
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Textarea rows={12} value={text} onChange={(x) => setText(x.target.value)} placeholder={t("admin.questions.explanationMarkdownLatex")} />
        <div className="rounded border border-line bg-snow p-2"><Md text={text || "…"} /></div>
      </div>
      <Btn variant="primary" disabled={!text.trim() || save.isPending} onClick={() => save.mutate()}>{t("admin.questions.saveLocale", { locale })}</Btn>
    </div>
  );
}

function StatusPanel({ q }: { q: Question }) {
  const t = useT();
  const [status, setStatus] = useState<Status>(q.status as Status);
  const [reason, setReason] = useState("");
  const act = useAct(() => bank.setStatus(q.id, status, reason), [["questions"], ["question", q.id]], t("admin.questions.statusChanged"));
  return (
    <div className="mt-3 max-w-lg space-y-3">
      <div className="grid grid-cols-2 gap-2 text-center text-sm sm:grid-cols-4">
        <Stat k={t("admin.questions.attempts")} v={q.attempts} /><Stat k={t("admin.questions.correct")} v={q.correct_rate == null ? "—" : `${Math.round(q.correct_rate * 100)}%`} /><Stat k={t("admin.questions.reports")} v={q.report_count} /><Stat k={t("admin.questions.officialKey")} v={q.answer_official ? t("admin.common.yes") : t("admin.common.no")} />
      </div>
      <Field label={t("admin.questions.newStatus")}><Select value={status} onChange={(e) => setStatus(e.target.value as Status)}>{QUESTION_STATUSES.map((s) => <option key={s}>{s}</option>)}</Select></Field>
      <Field label={t("admin.questions.reasonAudited")}><Input value={reason} onChange={(e) => setReason(e.target.value)} /></Field>
      <Btn variant="primary" disabled={status === q.status || act.isPending} onClick={() => act.mutate()}>{t("admin.questions.changeStatus")}</Btn>
    </div>
  );
}
const Stat = ({ k, v }: { k: string; v: React.ReactNode }) => <div className="rounded-xl border border-line p-2"><div className="text-xs uppercase text-ink-soft">{k}</div><div className="font-extrabold">{v}</div></div>;
