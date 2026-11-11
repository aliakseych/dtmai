"use client";
import { useState } from "react";
import { catalog, qk, useAct, useBases, type QBase, type QBaseIn } from "@/lib/catalog";
import { SOURCE_KINDS, nm } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader, Select } from "@/components/ui/controls";
import { Drawer } from "@/components/ui/overlay";
import { DataTable } from "@/components/ui/table";
import { NamesEditor, cleanNames } from "@/components/ui/names";

const blank: QBaseIn = { code: "", names: {}, kind: "previous_year", year: null, provenance: "", license_note: "", active: true, position: 0 };

export default function SourcesPage() {
  const q = useBases();
  const [edit, setEdit] = useState<{ id?: string; form: QBaseIn } | null>(null);
  const save = useAct(
    (e: { id?: string; form: QBaseIn }) => {
      const body = { ...e.form, names: cleanNames(e.form.names) };
      return e.id ? catalog.bases.update(e.id, body) : catalog.bases.create(body);
    },
    [qk.bases],
    "Saved",
  );
  const del = useAct((id: string) => catalog.bases.remove(id), [qk.bases], "Deleted");
  const f = edit?.form;
  const set = (p: Partial<QBaseIn>) => setEdit((e) => e && { ...e, form: { ...e.form, ...p } });
  const open = (s: QBase) => setEdit({ id: s.id, form: { code: s.code, names: s.names, kind: s.kind as QBaseIn["kind"], year: s.year, provenance: s.provenance ?? "", license_note: s.license_note ?? "", active: s.active, position: s.position } });

  return (
    <>
      <PageHeader title="Question bases" sub="Where questions come from: official papers, Bluebook, generated, harvested." actions={<Btn variant="primary" onClick={() => setEdit({ form: blank })}>New base</Btn>} />
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(r) => r.id} onRow={open}
          cols={[
            { key: "code", head: "Code", cell: (r) => <code>{r.code}</code> },
            { key: "name", head: "Name", cell: (r) => nm(r.names) },
            { key: "kind", head: "Kind", cell: (r) => <Badge tone="blue">{r.kind}</Badge> },
            { key: "year", head: "Year", cell: (r) => r.year ?? "—" },
            { key: "prov", head: "Provenance", cell: (r) => r.provenance ?? "—" },
            { key: "act", head: "State", cell: (r) => <Badge tone={r.active ? "green" : "gray"}>{r.active ? "active" : "inactive"}</Badge> },
          ]} />
      </div>
      <Drawer open={!!edit} onClose={() => setEdit(null)} width="max-w-lg" title={edit?.id ? "Edit base" : "New base"}
        footer={<>
          {edit?.id && <Btn variant="danger" className="mr-auto" onClick={() => confirm("Delete this base?") && del.mutate(edit.id!, { onSuccess: () => setEdit(null) })}>Delete</Btn>}
          <Btn onClick={() => setEdit(null)}>Cancel</Btn>
          <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(edit!, { onSuccess: () => setEdit(null) })}>Save</Btn>
        </>}>
        {f && (
          <div className="space-y-3">
            <Field label="Code"><Input value={f.code} onChange={(e) => set({ code: e.target.value })} /></Field>
            <NamesEditor value={f.names} onChange={(names) => set({ names })} />
            <div className="grid grid-cols-3 gap-3">
              <Field label="Kind"><Select value={f.kind} onChange={(e) => set({ kind: e.target.value as QBaseIn["kind"] })}>{SOURCE_KINDS.map((k) => <option key={k}>{k}</option>)}</Select></Field>
              <Field label="Year"><Input type="number" value={f.year ?? ""} onChange={(e) => set({ year: e.target.value ? Number(e.target.value) : null })} /></Field>
              <Field label="Position"><Input type="number" value={f.position ?? 0} onChange={(e) => set({ position: Number(e.target.value) })} /></Field>
            </div>
            <Field label="Provenance"><Input value={f.provenance ?? ""} onChange={(e) => set({ provenance: e.target.value })} /></Field>
            <Field label="License note"><Input value={f.license_note ?? ""} onChange={(e) => set({ license_note: e.target.value })} /></Field>
            <Check checked={f.active ?? true} onChange={(active) => set({ active })} label="Active" />
          </div>
        )}
      </Drawer>
    </>
  );
}
