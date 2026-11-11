"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { generation, type GenerationIn } from "@/lib/generation";
import { useAct, useSubjects, useTopics, useTypes } from "@/lib/catalog";
import { nm } from "@/lib/util";
import { Badge, Btn, Field, Input, PageHeader, Select, Textarea } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";
import { LangInput } from "@/components/ui/lang";

const TONE: Record<string, "gray" | "green" | "red" | "blue" | "gold"> = { queued: "gray", running: "blue", done: "green", failed: "red" };

export default function GenerationPage() {
  const subjects = useSubjects();
  const types = useTypes();
  const [f, setF] = useState<Partial<GenerationIn>>({ language: "uz-Latn", count: 10 });
  const topics = useTopics(f.subject_id);
  const runs = useQuery({ queryKey: ["generation-runs"], queryFn: () => generation.list(), refetchInterval: 5000 });
  const start = useAct((b: GenerationIn) => generation.start(b), [["generation-runs"]], "Generation queued");
  const set = (p: Partial<GenerationIn>) => setF((x) => ({ ...x, ...p }));
  const ready = f.subject_id && f.topic_id && f.type_id && f.language && (f.count ?? 0) > 0;
  const name = (list: { id: string; names: Record<string, string> }[] | undefined, id: string | null | undefined) => (id ? nm(list?.find((x) => x.id === id)?.names, id.slice(0, 8)) : "—");
  return (
    <>
      <PageHeader title="Generation runs" sub="AI-generate questions for a topic and type. Results land as auto_agreed / escalated in the labeling queue." actions={<Link href="/labeling/" className="text-sm font-extrabold text-blue-deep">Open labeling →</Link>} />
      <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">
        <div className="grid grid-cols-6 gap-3 rounded-xl border border-line bg-white p-4">
          <Field label="Subject"><Select value={f.subject_id ?? ""} onChange={(e) => set({ subject_id: e.target.value, topic_id: undefined })}><option value="">—</option>{subjects.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select></Field>
          <Field label="Topic"><Select value={f.topic_id ?? ""} onChange={(e) => set({ topic_id: e.target.value })}><option value="">—</option>{topics.data?.map((t) => <option key={t.id} value={t.id}>{nm(t.names)}</option>)}</Select></Field>
          <Field label="Question type"><Select value={f.type_id ?? ""} onChange={(e) => set({ type_id: e.target.value })}><option value="">—</option>{types.data?.map((t) => <option key={t.id} value={t.id}>{nm(t.names)} · {t.kind}</option>)}</Select></Field>
          <Field label="Language"><LangInput value={f.language ?? ""} onChange={(language) => set({ language })} /></Field>
          <Field label="Count"><Input type="number" min={1} max={200} value={f.count ?? 10} onChange={(e) => set({ count: Number(e.target.value) })} /></Field>
          <Field label="Difficulty (ELO, optional)"><Input type="number" value={f.difficulty ?? ""} onChange={(e) => set({ difficulty: e.target.value ? Number(e.target.value) : null })} /></Field>
          <Field label="Prompt template override (optional)" className="col-span-5"><Textarea rows={2} value={f.prompt_template ?? ""} onChange={(e) => set({ prompt_template: e.target.value || null })} /></Field>
          <div className="flex items-end"><Btn variant="primary" className="w-full" disabled={!ready || start.isPending} onClick={() => start.mutate(f as GenerationIn)}>Generate</Btn></div>
        </div>
        <DataTable rows={runs.data} loading={runs.isLoading} error={runs.error} rowKey={(r) => r.id} empty="No runs yet."
          cols={[
            { key: "s", head: "Subject", cell: (r) => name(subjects.data, r.subject_id) },
            { key: "t", head: "Topic", cell: (r) => name(topics.data, r.topic_id) },
            { key: "k", head: "Kind", cell: (r) => <Badge tone="blue">{r.kind}</Badge> },
            { key: "l", head: "Lang", cell: (r) => r.language },
            { key: "st", head: "Status", cell: (r) => <Badge tone={TONE[r.status] ?? "gray"}>{r.status}</Badge> },
            { key: "n", head: "Created / requested", cell: (r) => `${r.created_count} / ${r.requested}` },
            { key: "x", head: "Failed", cell: (r) => r.failed_count || "—" },
            { key: "e", head: "Error", cell: (r) => <span className="text-red-deep">{r.error ?? ""}</span> },
          ]} />
      </div>
    </>
  );
}
