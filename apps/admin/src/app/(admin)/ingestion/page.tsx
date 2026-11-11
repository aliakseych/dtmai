"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ingestion, type Batch, type BatchIn, type UploadIn } from "@/lib/ingestion";
import { useAct, useSubjects } from "@/lib/catalog";
import { nm } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader, Select } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";
import { Drawer } from "@/components/ui/overlay";


const TONE: Record<string, "gray" | "green" | "red" | "blue" | "gold"> = { queued: "gray", running: "blue", done: "green", failed: "red", partial: "gold" };
const blank: BatchIn = { root: "", source_code: "", source_name: null, source_year: null, subject_id: "", language: "uz", has_answer_key: false };

export default function IngestionPage() {
  const subjects = useSubjects();
  const list = useQuery({ queryKey: ["ingest-batches"], queryFn: () => ingestion.list(), refetchInterval: 5000 });
  const [open, setOpen] = useState(false);
  const [f, setF] = useState<BatchIn>(blank);
  const [sel, setSel] = useState<string | null>(null);
  const detail = useQuery({ queryKey: ["ingest-batch", sel], queryFn: () => ingestion.get(sel!), enabled: !!sel, refetchInterval: 5000 });
  const start = useAct((b: BatchIn) => ingestion.start(b), [["ingest-batches"]], "Ingestion queued");
  const upload = useAct((b: UploadIn) => ingestion.upload(b), [["ingest-batches"]], "Upload queued");
  const [files, setFiles] = useState<File[]>([]);
  const busy = start.isPending || upload.isPending;
  const addFiles = (l: FileList | null) => l && setFiles((p) => [...p, ...Array.from(l)].slice(0, 50));
  const done = () => { setOpen(false); setFiles([]); setF(blank); };
  const submit = () => {
    if (files.length) {
      const { root: _root, type_ids: _t, ...rest } = f;
      upload.mutate({ ...rest, files }, { onSuccess: done });
    } else start.mutate(f, { onSuccess: done });
  };
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
        footer={<><Btn onClick={() => setOpen(false)}>Cancel</Btn><Btn variant="primary" disabled={!(files.length || f.root) || !f.source_code || !f.subject_id || !f.language || busy} onClick={submit}>Start</Btn></>}>
        <div className="space-y-3">
          <Field label="Files" hint="PDF, PNG, JPEG or WebP · up to 50 files, 25 MB each.">
            <label onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); addFiles(e.dataTransfer.files); }}
              className="flex cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed border-gray-300 p-6 text-center text-sm">
              <span>Drop files here or click to choose</span>
              <input type="file" multiple accept="application/pdf,image/png,image/jpeg,image/webp" className="hidden" onChange={(e) => { addFiles(e.target.files); e.target.value = ""; }} />
            </label>
            {files.length > 0 && (
              <ul className="mt-2 space-y-1 text-sm">
                {files.map((x, i) => (
                  <li key={`${x.name}-${i}`} className="flex items-center justify-between gap-2">
                    <span className="break-all">{x.name} <span className="text-gray-500">({(x.size / 1024 / 1024).toFixed(1)} MB)</span></span>
                    <Btn onClick={() => setFiles((p) => p.filter((_, j) => j !== i))}>Remove</Btn>
                  </li>
                ))}
              </ul>
            )}
          </Field>
          <details>
            <summary className="cursor-pointer text-sm">Advanced</summary>
            <div className="mt-2">
              <Field label="Folder (server path)" hint="Optional. Used only when no files are uploaded; directory readable by the API worker, e.g. /data/math-2023."><Input value={f.root} onChange={(e) => set({ root: e.target.value })} /></Field>
            </div>
          </details>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Source code"><Input value={f.source_code} onChange={(e) => set({ source_code: e.target.value })} /></Field>
            <Field label="Source name"><Input value={f.source_name ?? ""} onChange={(e) => set({ source_name: e.target.value || null })} /></Field>
            <Field label="Year"><Input type="number" value={f.source_year ?? ""} onChange={(e) => set({ source_year: e.target.value ? Number(e.target.value) : null })} /></Field>
            <Field label="Subject"><Select value={f.subject_id} onChange={(e) => set({ subject_id: e.target.value })}><option value="">—</option>{subjects.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select></Field>
            <Field label="Language"><Select value={f.language} onChange={(e) => set({ language: e.target.value })}><option value="uz">uz</option><option value="ru">ru</option></Select></Field>
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
