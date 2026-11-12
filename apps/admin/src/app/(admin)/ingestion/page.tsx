"use client";
import { useEnum, useT } from "@/lib/i18n";
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
  const t = useT();
  const en = useEnum();
  const subjects = useSubjects();
  const [showArchived, setShowArchived] = useState(false);
  const list = useQuery({ queryKey: ["ingest-batches", showArchived], queryFn: () => ingestion.list(100, showArchived), refetchInterval: 5000 });
  const [open, setOpen] = useState(false);
  const [f, setF] = useState<BatchIn>(blank);
  const [sel, setSel] = useState<string | null>(null);
  const detail = useQuery({ queryKey: ["ingest-batch", sel], queryFn: () => ingestion.get(sel!), enabled: !!sel, refetchInterval: 5000 });
  const start = useAct((b: BatchIn) => ingestion.start(b), [["ingest-batches"]], t("admin.ingestion.ingestionQueued"));
  const upload = useAct((b: UploadIn) => ingestion.upload(b), [["ingest-batches"]], t("admin.ingestion.uploadQueued"));
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
  const rerun = useAct((a: { id: string; unfinished: boolean }) => ingestion.rerun(a.id, a.unfinished), [["ingest-batches"], ["ingest-batch"]], t("admin.ingestion.reRunQueued"));
  const archive = useAct((a: { id: string; on: boolean }) => (a.on ? ingestion.archive(a.id) : ingestion.unarchive(a.id)), [["ingest-batches"]], t("admin.common.saved"));
  const set = (p: Partial<BatchIn>) => setF((x) => ({ ...x, ...p }));
  return (
    <>
      <PageHeader title={t("admin.ingestion.ingestion")} sub={t("admin.ingestion.uploadExamPdfsOr")} actions={<div className="flex items-center gap-3"><Check checked={showArchived} onChange={setShowArchived} label={t("admin.common.showArchived")} /><Btn variant="primary" onClick={() => setOpen(true)}>{t("admin.ingestion.newBatch")}</Btn></div>} />
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable<Batch> rows={list.data} loading={list.isLoading} error={list.error} rowKey={(r) => r.id} onRow={(r) => setSel(r.id)} selected={sel}
          cols={[
            { key: "src", head: t("admin.common.source"), cell: (r) => <code>{r.source_code}</code> },
            { key: "s", head: t("admin.common.subject"), cell: (r) => nm(subjects.data?.find((s) => s.id === r.subject_id)?.names) },
            { key: "l", head: t("admin.common.lang"), cell: (r) => r.language },
            { key: "st", head: t("admin.common.status"), cell: (r) => <Badge tone={TONE[r.status] ?? "gray"}>{en("job", r.status)}</Badge> },
            { key: "f", head: t("admin.ingestion.files"), cell: (r) => `${r.files_done} / ${r.files_total}` },
            { key: "q", head: t("admin.ingestion.questions"), cell: (r) => r.questions_created },
            { key: "e", head: t("admin.common.error"), cell: (r) => <span className="text-red-deep">{r.error ?? ""}</span> },
            { key: "arch", head: "", cell: (r) => (r.status === "pending" || r.status === "running") ? null : <Btn onClick={(e) => { e.stopPropagation(); archive.mutate({ id: r.id, on: !r.archived }); }}>{r.archived ? t("admin.common.unarchive") : t("admin.common.archive")}</Btn> },
          ]} />
      </div>
      <Drawer open={open} onClose={() => setOpen(false)} width="max-w-lg" title={t("admin.ingestion.newIngestionBatch")}
        footer={<><Btn onClick={() => setOpen(false)}>{t("admin.common.cancel")}</Btn><Btn variant="primary" disabled={!(files.length || f.root) || !f.source_code || !f.subject_id || !f.language || busy} onClick={submit}>{t("admin.ingestion.start")}</Btn></>}>
        <div className="space-y-3">
          <Field label={t("admin.ingestion.files")} hint={t("admin.ingestion.pdfDocxPngJpeg")}>
            <label onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); addFiles(e.dataTransfer.files); }}
              className="relative flex cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed border-gray-300 p-6 text-center text-sm focus-within:outline focus-within:outline-2 focus-within:outline-blue">
              <span>{t("admin.ingestion.dropFilesHereOr")}</span>
              <input type="file" multiple accept="application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,image/png,image/jpeg,image/webp" className="sr-only" onChange={(e) => { addFiles(e.target.files); e.target.value = ""; }} />
            </label>
            {files.length > 0 && (
              <ul className="mt-2 space-y-1 text-sm">
                {files.map((x, i) => (
                  <li key={`${x.name}-${i}`} className="flex items-center justify-between gap-2">
                    <span className="break-all">{x.name} <span className="text-gray-500">{t("admin.ingestion.sizeMb", { n: (x.size / 1024 / 1024).toFixed(1) })}</span></span>
                    <Btn onClick={() => setFiles((p) => p.filter((_, j) => j !== i))}>{t("admin.common.remove")}</Btn>
                  </li>
                ))}
              </ul>
            )}
          </Field>
          <details>
            <summary className="cursor-pointer text-sm">{t("admin.ingestion.advanced")}</summary>
            <div className="mt-2">
              <Field label={t("admin.ingestion.folderServerPath")} hint={t("admin.ingestion.optionalUsedOnlyWhen")}><Input value={f.root} onChange={(e) => set({ root: e.target.value })} /></Field>
            </div>
          </details>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label={t("admin.ingestion.sourceCode")}><Input value={f.source_code} onChange={(e) => set({ source_code: e.target.value })} /></Field>
            <Field label={t("admin.ingestion.sourceName")}><Input value={f.source_name ?? ""} onChange={(e) => set({ source_name: e.target.value || null })} /></Field>
            <Field label={t("admin.common.year")}><Input type="number" value={f.source_year ?? ""} onChange={(e) => set({ source_year: e.target.value ? Number(e.target.value) : null })} /></Field>
            <Field label={t("admin.common.subject")}><Select value={f.subject_id} onChange={(e) => set({ subject_id: e.target.value })}><option value="">—</option>{subjects.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select></Field>
            <Field label={t("admin.common.language")}><Select value={f.language} onChange={(e) => set({ language: e.target.value })}><option value="uz">{t("admin.common.uz")}</option><option value="ru">{t("admin.common.ru")}</option></Select></Field>
            <Field label={t("admin.ingestion.questionBaseCode")}><Input value={f.base ?? ""} onChange={(e) => set({ base: e.target.value || null })} /></Field>
          </div>
          <Check checked={f.has_answer_key ?? false} onChange={(has_answer_key) => set({ has_answer_key })} label={t("admin.ingestion.filesContainAnAnswer")} />
        </div>
      </Drawer>
      <Drawer open={!!sel} onClose={() => setSel(null)} width="max-w-xl" title={t("admin.ingestion.batch", { code: detail.data?.source_code ?? "" })}
        footer={detail.data && <><Btn onClick={() => rerun.mutate({ id: detail.data!.id, unfinished: true })}>{t("admin.ingestion.reRunUnfinished")}</Btn><Btn onClick={() => rerun.mutate({ id: detail.data!.id, unfinished: false })}>{t("admin.ingestion.reRunFailedOnly")}</Btn></>}>
        <DataTable rows={detail.data?.files} loading={detail.isLoading} error={detail.error} rowKey={(r) => r.id}
          cols={[
            { key: "p", head: t("admin.ingestion.file"), cell: (r) => <span className="break-all">{r.path}</span> },
            { key: "s", head: t("admin.common.status"), cell: (r) => <Badge tone={TONE[r.status] ?? "gray"}>{en("job", r.status)}</Badge> },
            { key: "q", head: t("admin.ingestion.qs"), cell: (r) => r.questions },
            { key: "e", head: t("admin.common.error"), cell: (r) => <span className="text-red-deep">{r.error ?? ""}</span> },
          ]} />
      </Drawer>
    </>
  );
}
