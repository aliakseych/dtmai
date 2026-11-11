"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ingestion, type Batch, type BatchIn } from "@/lib/ingestion";
import { useAct, useSubjects } from "@/lib/catalog";
import { nm } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader, Select } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";
import { Drawer } from "@/components/ui/overlay";
import { LangInput } from "@/components/ui/lang";

const TONE: Record<string, "gray" | "green" | "red" | "blue" | "gold"> = { queued: "gray", running: "blue", done: "green", failed: "red", partial: "gold" };
const blank: BatchIn = { root: "", source_code: "", source_name: null, source_year: null, subject_id: "", language: "uz-Latn", has_answer_key: false };

export default function IngestionPage() {
  const subjects = useSubjects();
  const list = useQuery({ queryKey: ["ingest-batches"], queryFn: () => ingestion.list(), refetchInterval: 5000 });
  const [open, setOpen] = useState(false);
  const [f, setF] = useState<BatchIn>(blank);
  const [sel, setSel] = useState<string | null>(null);
  const detail = useQuery({ queryKey: ["ingest-batch", sel], queryFn: () => ingestion.get(sel!), enabled: !!sel, refetchInterval: 5000 });
  const start = useAct((b: BatchIn) => ingestion.start(b), [["ingest-batches"]], "Ingestion queued");
  const rerun = useAct((a: { id: string; unfinished: boolean }) => ingestion.rerun(a.id, a.unfinished), [["ingest-batches"], ["ingest-batch"]], "Re-run queued");
  const set = (p: Partial<BatchIn>) => setF((x) => ({ ...x, ...p }));
  return (
    <>
      <PageHeader title="Ingestion" sub="Harvest question files from a server-side folder through the AI extraction pipeline." actions={<Btn variant="primary" onClick={() => setOpen(true)}>New batch</Btn>} />
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable<Batch> rows={list.data} loading={list.isLoading} error={list.error} rowKey={(r) => r.id} onRow={(r) => setSel(r.id)} selected={sel}
          cols={[
            { key: "src", head: "Source", cell: (r) => <code>{r.source_code}</code> },
            { key: "s", head: "Subject", cell: (r) => nm(subjects.data?.find((s) => s.id === r.subject_id)?.names) },
            { key: "l", head: "Lang", cell: (r) => r.language },
            { key: "st", head: "Status", cell: (r) => <Badge tone={TONE[r.status] ?? "gray"}>{r.status}</Badge> },
            { key: "f", head: "Files", cell: (r) => `${r.files_done} / ${r.files_total}` },
            { key: "q", head: "Questions", cell: (r) => r.questions_created },
            { key: "e", head: "Error", cell: (r) => <span className="text-red-deep">{r.error ?? ""}</span> },
          ]} />
      </div>
      <Drawer open={open} onClose={() => setOpen(false)} width="max-w-lg" title="New ingestion batch"
        footer={<><Btn onClick={() => setOpen(false)}>Cancel</Btn><Btn variant="primary" disabled={!f.root || !f.source_code || !f.subject_id || start.isPending} onClick={() => start.mutate(f, { onSuccess: () => setOpen(false) })}>Start</Btn></>}>
        <div className="space-y-3">
          <Field label="Folder (server path)" hint="Directory readable by the API worker, e.g. /data/math-2023."><Input value={f.root} onChange={(e) => set({ root: e.target.value })} /></Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Source code"><Input value={f.source_code} onChange={(e) => set({ source_code: e.target.value })} /></Field>
            <Field label="Source name"><Input value={f.source_name ?? ""} onChange={(e) => set({ source_name: e.target.value || null })} /></Field>
            <Field label="Year"><Input type="number" value={f.source_year ?? ""} onChange={(e) => set({ source_year: e.target.value ? Number(e.target.value) : null })} /></Field>
            <Field label="Subject"><Select value={f.subject_id} onChange={(e) => set({ subject_id: e.target.value })}><option value="">—</option>{subjects.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select></Field>
            <Field label="Language"><LangInput value={f.language} onChange={(language) => set({ language })} /></Field>
            <Field label="Question base code"><Input value={f.base ?? ""} onChange={(e) => set({ base: e.target.value || null })} /></Field>
          </div>
          <Check checked={f.has_answer_key ?? false} onChange={(has_answer_key) => set({ has_answer_key })} label="Files contain an answer key" />
        </div>
      </Drawer>
      <Drawer open={!!sel} onClose={() => setSel(null)} width="max-w-xl" title={`Batch ${detail.data?.source_code ?? ""}`}
        footer={detail.data && <><Btn onClick={() => rerun.mutate({ id: detail.data!.id, unfinished: true })}>Re-run unfinished</Btn><Btn onClick={() => rerun.mutate({ id: detail.data!.id, unfinished: false })}>Re-run failed only</Btn></>}>
        <DataTable rows={detail.data?.files} loading={detail.isLoading} error={detail.error} rowKey={(r) => r.id}
          cols={[
            { key: "p", head: "File", cell: (r) => <span className="break-all">{r.path}</span> },
            { key: "s", head: "Status", cell: (r) => <Badge tone={TONE[r.status] ?? "gray"}>{r.status}</Badge> },
            { key: "q", head: "Qs", cell: (r) => r.questions },
            { key: "e", head: "Error", cell: (r) => <span className="text-red-deep">{r.error ?? ""}</span> },
          ]} />
      </Drawer>
    </>
  );
}
