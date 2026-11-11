"use client";
import { useState } from "react";
import { catalog, qk, useAct, useSubjects, type Subject, type SubjectIn } from "@/lib/catalog";
import { nm } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader } from "@/components/ui/controls";
import { Drawer } from "@/components/ui/overlay";
import { DataTable } from "@/components/ui/table";
import { NamesEditor, cleanNames } from "@/components/ui/names";

const blank: SubjectIn = { code: "", names: {}, weight: 1, active: true, position: 0 };

export default function SubjectsPage() {
  const q = useSubjects();
  const [edit, setEdit] = useState<{ id?: string; form: SubjectIn } | null>(null);
  const save = useAct(
    (e: { id?: string; form: SubjectIn }) => {
      const body = { ...e.form, names: cleanNames(e.form.names) };
      return e.id ? catalog.subjects.update(e.id, body) : catalog.subjects.create(body);
    },
    [qk.subjects],
    "Saved",
  );
  const del = useAct((id: string) => catalog.subjects.remove(id), [qk.subjects], "Deleted");
  const rows = [...(q.data ?? [])].sort((a, b) => a.position - b.position);
  const f = edit?.form;
  const set = (p: Partial<SubjectIn>) => setEdit((e) => e && { ...e, form: { ...e.form, ...p } });
  const open = (s: Subject) => setEdit({ id: s.id, form: { code: s.code, names: s.names, weight: s.weight, active: s.active, position: s.position } });

  return (
    <>
      <PageHeader title="Subjects" sub="Weight drives the predicted-score blend; order drives the learner picker." actions={<Btn variant="primary" onClick={() => setEdit({ form: { ...blank, position: rows.length } })}>New subject</Btn>} />
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={rows} loading={q.isLoading} error={q.error} rowKey={(r) => r.id} onRow={open}
          cols={[
            { key: "pos", head: "#", cell: (r) => r.position, className: "w-12" },
            { key: "code", head: "Code", cell: (r) => <code>{r.code}</code> },
            { key: "name", head: "Name", cell: (r) => nm(r.names) },
            { key: "w", head: "Weight", cell: (r) => r.weight },
            { key: "act", head: "State", cell: (r) => <Badge tone={r.active ? "green" : "gray"}>{r.active ? "active" : "inactive"}</Badge> },
          ]} />
      </div>
      <Drawer open={!!edit} onClose={() => setEdit(null)} width="max-w-lg" title={edit?.id ? "Edit subject" : "New subject"}
        footer={<>
          {edit?.id && <Btn variant="danger" className="mr-auto" onClick={() => confirm("Delete this subject?") && del.mutate(edit.id!, { onSuccess: () => setEdit(null) })}>Delete</Btn>}
          <Btn onClick={() => setEdit(null)}>Cancel</Btn>
          <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(edit!, { onSuccess: () => setEdit(null) })}>Save</Btn>
        </>}>
        {f && (
          <div className="space-y-3">
            <Field label="Code" hint="lowercase, digits, _ or -"><Input value={f.code} onChange={(e) => set({ code: e.target.value })} /></Field>
            <NamesEditor value={f.names} onChange={(names) => set({ names })} />
            <div className="grid grid-cols-2 gap-3">
              <Field label="Weight"><Input type="number" step="0.1" min={0} value={f.weight} onChange={(e) => set({ weight: Number(e.target.value) })} /></Field>
              <Field label="Position"><Input type="number" value={f.position ?? 0} onChange={(e) => set({ position: Number(e.target.value) })} /></Field>
            </div>
            <Check checked={f.active} onChange={(active) => set({ active })} label="Active" />
          </div>
        )}
      </Drawer>
    </>
  );
}
