"use client";
import { useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useAct, useBases, useSubjects, useTopics, useTypes, type Question } from "@/lib/catalog";
import { bank, type QFilters, type Status } from "@/lib/questions";
import { QUESTION_KINDS, QUESTION_STATUSES, nm } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader, Select, StatusBadge, Textarea, Toolbar } from "@/components/ui/controls";
import { Dialog } from "@/components/ui/overlay";
import { DataTable } from "@/components/ui/table";
import { LangInput } from "@/components/ui/lang";
import { QuestionEditor } from "@/components/questions/QuestionEditor";

const PAGE = 50;
export default function QuestionsPage() {
  return <Suspense><Bank /></Suspense>;
}

function Bank() {
  const sp = useSearchParams();
  const router = useRouter();
  const [f, setF] = useState<Omit<QFilters, "limit" | "offset">>(() => ({
    subject_id: sp.get("subject_id") ?? "", topic_id: sp.get("topic_id") ?? "", type_id: sp.get("type_id") ?? "", language: sp.get("language") ?? "",
    status: (sp.get("status") as Status) || undefined, source_id: "", kind: "", q: "", reported: false,
  }));
  const [page, setPage] = useState(0);
  const [sel, setSel] = useState<Set<string>>(new Set());
  const [editing, setEditing] = useState<string | null>(sp.get("new") ? "new" : sp.get("id"));
  const [importing, setImporting] = useState(false);
  const [bulk, setBulk] = useState<Status | "">("");
  const setFilter = (p: Partial<typeof f>) => { setF((x) => ({ ...x, ...p })); setPage(0); setSel(new Set()); };
  const subjects = useSubjects(), types = useTypes(), bases = useBases(), topics = useTopics(f.subject_id || undefined);
  const list = useQuery({ queryKey: ["questions", f, page], queryFn: () => bank.list({ ...f, limit: PAGE, offset: page * PAGE }), placeholderData: (p) => p });
  const bulkAct = useAct((s: Status) => bank.bulkStatus([...sel], s, "bulk action from admin table"), [["questions"]], "Updated");
  const subjName = useMemo(() => new Map(subjects.data?.map((s) => [s.id, nm(s.names)])), [subjects.data]);
  useEffect(() => { if (sp.get("new") || sp.get("id")) router.replace("/questions/"); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const rows = list.data?.items;
  const allSel = !!rows?.length && rows.every((r) => sel.has(r.id));
  const toggle = (id: string) => setSel((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });
  const total = list.data?.total ?? 0;

  return (
    <>
      <PageHeader title="Question bank" sub={`${total.toLocaleString()} questions match`} actions={<><Btn onClick={() => setImporting(true)}>Import JSON</Btn><Btn variant="primary" onClick={() => setEditing("new")}>New question</Btn></>} />
      <Toolbar>
        <Field label="Search"><Input value={f.q ?? ""} onChange={(e) => setFilter({ q: e.target.value })} placeholder="stem contains…" /></Field>
        <Field label="Subject"><Select value={f.subject_id} onChange={(e) => setFilter({ subject_id: e.target.value, topic_id: "" })}><option value="">All</option>{subjects.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select></Field>
        <Field label="Topic"><Select value={f.topic_id} disabled={!f.subject_id} onChange={(e) => setFilter({ topic_id: e.target.value })}><option value="">All</option>{topics.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select></Field>
        <Field label="Type"><Select value={f.type_id} onChange={(e) => setFilter({ type_id: e.target.value })}><option value="">All</option>{types.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select></Field>
        <Field label="Kind"><Select value={f.kind} onChange={(e) => setFilter({ kind: e.target.value })}><option value="">All</option>{QUESTION_KINDS.map((k) => <option key={k}>{k}</option>)}</Select></Field>
        <Field label="Language"><LangInput value={f.language ?? ""} onChange={(language) => setFilter({ language })} /></Field>
        <Field label="Status"><Select value={f.status ?? ""} onChange={(e) => setFilter({ status: (e.target.value || undefined) as Status | undefined })}><option value="">All</option>{QUESTION_STATUSES.map((k) => <option key={k}>{k}</option>)}</Select></Field>
        <Field label="Source"><Select value={f.source_id} onChange={(e) => setFilter({ source_id: e.target.value })}><option value="">All</option>{bases.data?.map((b) => <option key={b.id} value={b.id}>{nm(b.names)}</option>)}</Select></Field>
        <div className="pb-1.5"><Check checked={!!f.reported} onChange={(reported) => setFilter({ reported })} label="Reported" /></div>
      </Toolbar>
      {sel.size > 0 && (
        <div className="flex items-center gap-2 border-b border-line bg-blue-soft px-4 py-1.5 text-sm">
          <b>{sel.size} selected</b>
          <Select className="w-40" value={bulk} onChange={(e) => setBulk(e.target.value as Status)}><option value="">Set status…</option>{QUESTION_STATUSES.map((s) => <option key={s}>{s}</option>)}</Select>
          <Btn variant="primary" disabled={!bulk || bulkAct.isPending} onClick={() => confirm(`Set ${sel.size} questions to ${bulk}?`) && bulkAct.mutate(bulk as Status, { onSuccess: () => setSel(new Set()) })}>Apply</Btn>
          <Btn variant="ghost" onClick={() => setSel(new Set())}>Clear</Btn>
        </div>
      )}
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={rows} loading={list.isLoading} error={list.error} rowKey={(r) => r.id} onRow={(r) => setEditing(r.id)}
          cols={[
            { key: "c", className: "w-8", head: <input type="checkbox" aria-label="Select page" checked={allSel} onChange={() => setSel(allSel ? new Set() : new Set(rows!.map((r) => r.id)))} />, cell: (r: Question) => <span onClick={(e) => e.stopPropagation()}><input type="checkbox" aria-label="Select" checked={sel.has(r.id)} onChange={() => toggle(r.id)} /></span> },
            { key: "stem", head: "Stem", cell: (r) => <span className="line-clamp-2 max-w-xl">{r.stem}</span> },
            { key: "subj", head: "Subject", cell: (r) => subjName.get(r.subject_id) ?? "—" },
            { key: "k", head: "Kind", cell: (r) => <Badge tone="blue">{r.kind}</Badge> },
            { key: "l", head: "Lang", cell: (r) => r.language },
            { key: "d", head: "Diff", cell: (r) => Math.round(r.difficulty) },
            { key: "st", head: "Status", cell: (r) => <StatusBadge status={r.status} /> },
            { key: "r", head: "Rep.", cell: (r) => (r.report_count ? <Badge tone="red">{r.report_count}</Badge> : "") },
            { key: "n", head: "Tries", cell: (r) => r.attempts },
          ]} />
      </div>
      <div className="flex items-center justify-end gap-2 border-t border-line px-4 py-1.5 text-sm">
        <span className="text-ink-soft">{total ? `${page * PAGE + 1}–${Math.min(total, (page + 1) * PAGE)} of ${total}` : "0"}</span>
        <Btn disabled={page === 0} onClick={() => setPage(page - 1)}>Prev</Btn>
        <Btn disabled={(page + 1) * PAGE >= total} onClick={() => setPage(page + 1)}>Next</Btn>
      </div>
      <QuestionEditor id={editing} preset={{ subject_id: f.subject_id, topic_id: f.topic_id, type_id: f.type_id, language: f.language || "uz-Latn" }} onClose={() => setEditing(null)} />
      <ImportDialog open={importing} onClose={() => setImporting(false)} />
    </>
  );
}

function ImportDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [text, setText] = useState("");
  const [parseErr, setParseErr] = useState<string | null>(null);
  const run = useAct((items: Record<string, unknown>[]) => bank.import(items), [["questions"]]);
  const go = () => {
    try {
      const v = JSON.parse(text);
      const items = Array.isArray(v) ? v : Array.isArray(v?.items) ? v.items : null;
      if (!items) throw new Error("Expected a JSON array (or {items:[…]})");
      setParseErr(null);
      run.mutate(items);
    } catch (e) { setParseErr((e as Error).message); }
  };
  return (
    <Dialog open={open} onClose={onClose} title="Import questions (JSON)" footer={<><Btn onClick={onClose}>Close</Btn><Btn variant="primary" disabled={!text.trim() || run.isPending} onClick={go}>Import</Btn></>}>
      <p className="mb-2 text-xs text-ink-soft">Array of question bodies (same shape as the editor payload). Each item is validated; failures are listed by index, imported ones land as drafts.</p>
      <Textarea rows={12} className="font-mono text-xs" value={text} onChange={(e) => setText(e.target.value)} />
      <input type="file" accept="application/json" className="mt-2 text-xs" onChange={async (e) => { const f = e.target.files?.[0]; if (f) setText(await f.text()); }} />
      {parseErr && <p className="mt-2 text-sm text-red-deep">{parseErr}</p>}
      {run.data && <div className="mt-2 text-sm"><b>{run.data.created.length} created</b>, {run.data.errors.length} failed
        <ul className="mt-1 max-h-40 overflow-auto text-xs text-red-deep">{run.data.errors.map((er) => <li key={er.index}>#{er.index}: {er.error}</li>)}</ul></div>}
    </Dialog>
  );
}
