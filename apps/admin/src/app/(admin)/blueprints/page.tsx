"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { catalog, qk, useAct, useBases, useSubjects, useTopics, useTypes, type Blueprint, type BlueprintIn } from "@/lib/catalog";
import { BLUEPRINT_KINDS, nm } from "@/lib/util";
import { Badge, Btn, Field, Input, PageHeader, Select, StatusBadge } from "@/components/ui/controls";
import { Drawer } from "@/components/ui/overlay";
import { DataTable } from "@/components/ui/table";
import { NamesEditor, cleanNames } from "@/components/ui/names";
import { MultiPick } from "@/components/ui/multipick";

interface Section { subject_id: string; topic_ids: string[]; type_ids: string[]; count: number; weight: number; question_ids?: string[] }
const blankSection = (subject_id: string): Section => ({ subject_id, topic_ids: [], type_ids: [], count: 10, weight: 1 });
const blank: BlueprintIn = { code: "", names: {}, kind: "generated", sections: [], duration_min: 60, source_id: null };

export default function BlueprintsPage() {
  const q = useQuery({ queryKey: qk.blueprints, queryFn: catalog.blueprints.list });
  const [edit, setEdit] = useState<{ id?: string; status?: string; version?: number; form: BlueprintIn } | null>(null);
  const inv = [qk.blueprints];
  const save = useAct((e: NonNullable<typeof edit>) => {
    const body = { ...e.form, names: cleanNames(e.form.names) };
    return e.id ? catalog.blueprints.update(e.id, body) : catalog.blueprints.create(body);
  }, inv, "Saved");
  const publish = useAct((id: string) => catalog.blueprints.publish(id), inv, "Published");
  const clone = useAct((id: string) => catalog.blueprints.clone(id), inv, "Cloned as draft");
  const del = useAct((id: string) => catalog.blueprints.remove(id), inv, "Deleted");
  const locked = edit?.status === "published";
  const f = edit?.form;
  const set = (p: Partial<BlueprintIn>) => setEdit((e) => e && { ...e, form: { ...e.form, ...p } });
  const sections = (f?.sections ?? []) as unknown as Section[];
  const setSections = (s: Section[]) => set({ sections: s as unknown as BlueprintIn["sections"] });
  const bases = useBases();
  const subjects = useSubjects();
  const open = (b: Blueprint) => setEdit({ id: b.id, status: b.status, version: b.version, form: { code: b.code, names: b.names, kind: b.kind as BlueprintIn["kind"], sections: b.sections, duration_min: b.duration_min, source_id: b.source_id ?? null } });

  return (
    <>
      <PageHeader title="Mock blueprints" sub="Draft → publish creates the next version. Published versions are immutable; clone to revise." actions={<Btn variant="primary" onClick={() => setEdit({ form: blank })}>New blueprint</Btn>} />
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(r) => r.id} onRow={open}
          cols={[
            { key: "code", head: "Code", cell: (r) => <code>{r.code}</code> },
            { key: "name", head: "Name", cell: (r) => nm(r.names) },
            { key: "kind", head: "Kind", cell: (r) => <Badge tone="blue">{r.kind}</Badge> },
            { key: "v", head: "Version", cell: (r) => (r.status === "published" ? `v${r.version}` : "—") },
            { key: "st", head: "Status", cell: (r) => <StatusBadge status={r.status} /> },
            { key: "d", head: "Min", cell: (r) => r.duration_min },
            { key: "s", head: "Sections", cell: (r) => r.sections.length },
          ]} />
      </div>
      <Drawer open={!!edit} onClose={() => setEdit(null)} title={`${edit?.id ? "Blueprint" : "New blueprint"}${edit?.status ? ` · ${edit.status}` : ""}`}
        footer={<>
          {edit?.id && <Btn variant="danger" className="mr-auto" onClick={() => confirm("Delete blueprint?") && del.mutate(edit.id!, { onSuccess: () => setEdit(null) })}>Delete</Btn>}
          <Btn onClick={() => setEdit(null)}>Close</Btn>
          {edit?.id && <Btn onClick={() => clone.mutate(edit.id!, { onSuccess: () => setEdit(null) })}>Clone as draft</Btn>}
          {edit?.id && !locked && <Btn onClick={() => confirm("Publish this draft as the next version?") && publish.mutate(edit.id!, { onSuccess: () => setEdit(null) })}>Publish</Btn>}
          {!locked && <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(edit!, { onSuccess: () => setEdit(null) })}>Save</Btn>}
        </>}>
        {f && (
          <fieldset disabled={locked} className="space-y-3">
            <div className="grid grid-cols-4 gap-3">
              <Field label="Code"><Input value={f.code} onChange={(e) => set({ code: e.target.value })} /></Field>
              <Field label="Kind"><Select value={f.kind} onChange={(e) => set({ kind: e.target.value as BlueprintIn["kind"] })}>{BLUEPRINT_KINDS.map((k) => <option key={k}>{k}</option>)}</Select></Field>
              <Field label="Duration (min)"><Input type="number" min={1} value={f.duration_min} onChange={(e) => set({ duration_min: Number(e.target.value) })} /></Field>
              <Field label="Source"><Select value={f.source_id ?? ""} onChange={(e) => set({ source_id: e.target.value || null })}><option value="">—</option>{bases.data?.map((b) => <option key={b.id} value={b.id}>{nm(b.names)}</option>)}</Select></Field>
            </div>
            <NamesEditor value={f.names} onChange={(names) => set({ names })} />
            <div className="flex items-center justify-between"><h3 className="text-sm">Sections ({sections.length})</h3>
              <Btn onClick={() => subjects.data?.[0] && setSections([...sections, blankSection(subjects.data[0].id)])}>Add section</Btn></div>
            {sections.map((s, i) => (
              <SectionEditor key={i} s={s} onChange={(n) => setSections(sections.map((x, j) => (j === i ? n : x)))} onRemove={() => setSections(sections.filter((_, j) => j !== i))} />
            ))}
            <p className="text-xs text-ink-soft">Total: {sections.reduce((a, s) => a + (s.count || 0), 0)} questions. Official papers pin exact <code>question_ids</code> (count must match).</p>
          </fieldset>
        )}
      </Drawer>
    </>
  );
}

function SectionEditor({ s, onChange, onRemove }: { s: Section; onChange: (s: Section) => void; onRemove: () => void }) {
  const subjects = useSubjects();
  const topics = useTopics(s.subject_id);
  const types = useTypes();
  return (
    <div className="space-y-2 rounded-md border border-line p-2">
      <div className="grid grid-cols-[1fr_6rem_6rem_auto] items-end gap-2">
        <Field label="Subject"><Select value={s.subject_id} onChange={(e) => onChange({ ...s, subject_id: e.target.value, topic_ids: [] })}>{subjects.data?.map((x) => <option key={x.id} value={x.id}>{nm(x.names)}</option>)}</Select></Field>
        <Field label="Count"><Input type="number" min={1} value={s.count} onChange={(e) => onChange({ ...s, count: Number(e.target.value) })} /></Field>
        <Field label="Weight"><Input type="number" step="0.1" min={0} value={s.weight} onChange={(e) => onChange({ ...s, weight: Number(e.target.value) })} /></Field>
        <Btn variant="danger" onClick={onRemove}>Remove</Btn>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <Field label="Topics"><MultiPick options={(topics.data ?? []).map((t) => ({ id: t.id, label: nm(t.names) }))} value={s.topic_ids} onChange={(topic_ids) => onChange({ ...s, topic_ids })} /></Field>
        <Field label="Types"><MultiPick options={(types.data ?? []).map((t) => ({ id: t.id, label: nm(t.names) }))} value={s.type_ids} onChange={(type_ids) => onChange({ ...s, type_ids })} /></Field>
      </div>
      {s.question_ids && <p className="text-xs text-ink-soft">{s.question_ids.length} pinned question ids</p>}
    </div>
  );
}
