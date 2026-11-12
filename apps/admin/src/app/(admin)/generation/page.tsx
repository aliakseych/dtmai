"use client";
import { useEnum, useT } from "@/lib/i18n";
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
  const t = useT();
  const en = useEnum();
  const subjects = useSubjects();
  const types = useTypes();
  const [f, setF] = useState<Partial<GenerationIn>>({ language: "uz-Latn", count: 10 });
  const topics = useTopics(f.subject_id);
  const runs = useQuery({ queryKey: ["generation-runs"], queryFn: () => generation.list(), refetchInterval: 5000 });
  const start = useAct((b: GenerationIn) => generation.start(b), [["generation-runs"]], t("admin.generation.generationQueued"));
  const set = (p: Partial<GenerationIn>) => setF((x) => ({ ...x, ...p }));
  const ready = f.subject_id && f.topic_id && f.type_id && f.language && (f.count ?? 0) > 0;
  const name = (list: { id: string; names: Record<string, string> }[] | undefined, id: string | null | undefined) => (id ? nm(list?.find((x) => x.id === id)?.names, id.slice(0, 8)) : "—");
  return (
    <>
      <PageHeader title={t("admin.generation.generationRuns")} sub={t("admin.generation.aiGenerateQuestionsFor")} actions={<Link href="/labeling/" className="text-sm font-extrabold text-blue-deep">{t("admin.generation.openLabeling")}</Link>} />
      <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">
        <div className="grid grid-cols-1 sm:grid-cols-6 gap-3 rounded-xl border border-line bg-white p-4">
          <Field label={t("admin.common.subject")}><Select value={f.subject_id ?? ""} onChange={(e) => set({ subject_id: e.target.value, topic_id: undefined })}><option value="">—</option>{subjects.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select></Field>
          <Field label={t("admin.common.topic")}><Select value={f.topic_id ?? ""} onChange={(e) => set({ topic_id: e.target.value })}><option value="">—</option>{topics.data?.map((t) => <option key={t.id} value={t.id}>{nm(t.names)}</option>)}</Select></Field>
          <Field label={t("admin.generation.questionType")}><Select value={f.type_id ?? ""} onChange={(e) => set({ type_id: e.target.value })}><option value="">—</option>{types.data?.map((t) => <option key={t.id} value={t.id}>{nm(t.names)} · {en("kind", t.kind)}</option>)}</Select></Field>
          <Field label={t("admin.common.language")}><LangInput value={f.language ?? ""} onChange={(language) => set({ language })} /></Field>
          <Field label={t("admin.common.count")}><Input type="number" min={1} max={200} value={f.count ?? 10} onChange={(e) => set({ count: Number(e.target.value) })} /></Field>
          <Field label={t("admin.generation.difficultyEloOptional")}><Input type="number" value={f.difficulty ?? ""} onChange={(e) => set({ difficulty: e.target.value ? Number(e.target.value) : null })} /></Field>
          <Field label={t("admin.generation.promptTemplateOverrideOptional")} className="sm:col-span-5"><Textarea rows={2} value={f.prompt_template ?? ""} onChange={(e) => set({ prompt_template: e.target.value || null })} /></Field>
          <div className="flex items-end"><Btn variant="primary" className="w-full" disabled={!ready || start.isPending} onClick={() => start.mutate(f as GenerationIn)}>{t("admin.generation.generate")}</Btn></div>
        </div>
        <DataTable rows={runs.data} loading={runs.isLoading} error={runs.error} rowKey={(r) => r.id} empty={t("admin.generation.noRunsYet")}
          cols={[
            { key: "s", head: t("admin.common.subject"), cell: (r) => name(subjects.data, r.subject_id) },
            { key: "t", head: t("admin.common.topic"), cell: (r) => name(topics.data, r.topic_id) },
            { key: "k", head: t("admin.common.kind"), cell: (r) => <Badge tone="blue">{en("kind", r.kind)}</Badge> },
            { key: "l", head: t("admin.common.lang"), cell: (r) => r.language },
            { key: "st", head: t("admin.common.status"), cell: (r) => <Badge tone={TONE[r.status] ?? "gray"}>{r.status}</Badge> },
            { key: "n", head: t("admin.generation.createdRequested"), cell: (r) => `${r.created_count} / ${r.requested}` },
            { key: "x", head: t("admin.generation.failed"), cell: (r) => r.failed_count || "—" },
            { key: "e", head: t("admin.common.error"), cell: (r) => <span className="text-red-deep">{r.error ?? ""}</span> },
          ]} />
      </div>
    </>
  );
}
