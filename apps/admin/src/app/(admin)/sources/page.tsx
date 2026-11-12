"use client";
import { useEnum, useT } from "@/lib/i18n";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { catalog, qk, useAct, type QBase, type QBaseIn } from "@/lib/catalog";
import { SOURCE_KINDS, nm } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader, Select } from "@/components/ui/controls";
import { Drawer } from "@/components/ui/overlay";
import { useConfirm } from "@/components/ui/confirm";
import { DataTable } from "@/components/ui/table";
import { NamesEditor, cleanNames } from "@/components/ui/names";

const blank: QBaseIn = { code: "", names: {}, kind: "previous_year", year: null, provenance: "", license_note: "", active: true, position: 0 };

export default function SourcesPage() {
  const t = useT();
  const en = useEnum();
  const [ask, confirmNode] = useConfirm();
  const [showArchived, setShowArchived] = useState(false);
  const q = useQuery({ queryKey: [...qk.bases, "admin", showArchived], queryFn: () => catalog.bases.list(showArchived) });
  const archive = useAct((a: { id: string; on: boolean }) => (a.on ? catalog.bases.archive(a.id) : catalog.bases.unarchive(a.id)), [qk.bases], t("admin.common.saved"));
  const [edit, setEdit] = useState<{ id?: string; form: QBaseIn } | null>(null);
  const save = useAct(
    (e: { id?: string; form: QBaseIn }) => {
      const body = { ...e.form, names: cleanNames(e.form.names) };
      return e.id ? catalog.bases.update(e.id, body) : catalog.bases.create(body);
    },
    [qk.bases],
    t("admin.common.saved"),
  );
  const del = useAct((id: string) => catalog.bases.remove(id), [qk.bases], t("admin.common.deleted"));
  const f = edit?.form;
  const set = (p: Partial<QBaseIn>) => setEdit((e) => e && { ...e, form: { ...e.form, ...p } });
  const open = (s: QBase) => setEdit({ id: s.id, form: { code: s.code, names: s.names, kind: s.kind as QBaseIn["kind"], year: s.year, provenance: s.provenance ?? "", license_note: s.license_note ?? "", active: s.active, position: s.position } });

  return (
    <>
      <PageHeader title={t("admin.sources.questionBases")} sub={t("admin.sources.whereQuestionsComeFrom")} actions={<div className="flex items-center gap-3"><Check checked={showArchived} onChange={setShowArchived} label={t("admin.common.showArchived")} /><Btn variant="primary" onClick={() => setEdit({ form: blank })}>{t("admin.sources.newBase")}</Btn></div>} />
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(r) => r.id} onRow={open}
          cols={[
            { key: "code", head: t("admin.common.code"), cell: (r) => <code>{r.code}</code> },
            { key: "name", head: t("admin.common.name"), cell: (r) => nm(r.names) },
            { key: "kind", head: t("admin.common.kind"), cell: (r) => <Badge tone="blue">{en("sourceKind", r.kind)}</Badge> },
            { key: "year", head: t("admin.common.year"), cell: (r) => r.year ?? "—" },
            { key: "prov", head: t("admin.sources.provenance"), cell: (r) => r.provenance ?? "—" },
            { key: "act", head: t("admin.common.state"), cell: (r) => r.archived ? <Badge tone="gray">{t("admin.common.archived")}</Badge> : <Badge tone={r.active ? "green" : "gray"}>{r.active ? t("admin.common.active") : t("admin.topics.inactive")}</Badge> },
            { key: "arch", head: "", cell: (r) => <Btn onClick={(e) => { e.stopPropagation(); archive.mutate({ id: r.id, on: !r.archived }); }}>{r.archived ? t("admin.common.unarchive") : t("admin.common.archive")}</Btn> },
          ]} />
      </div>
      <Drawer open={!!edit} onClose={() => setEdit(null)} width="max-w-lg" title={edit?.id ? t("admin.sources.editBase") : t("admin.sources.newBase")}
        footer={<>
          {edit?.id && <Btn variant="danger" className="mr-auto" onClick={() => ask({ title: t("admin.sources.deleteThisBase"), name: nm(edit.form.names) || edit.form.code, danger: true, confirmLabel: t("admin.common.delete") }, () => del.mutate(edit.id!, { onSuccess: () => setEdit(null) }))}>{t("admin.common.delete")}</Btn>}
          <Btn onClick={() => setEdit(null)}>{t("admin.common.cancel")}</Btn>
          <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(edit!, { onSuccess: () => setEdit(null) })}>{t("admin.common.save")}</Btn>
        </>}>
        {f && (
          <div className="space-y-3">
            <Field label={t("admin.common.code")}><Input value={f.code} onChange={(e) => set({ code: e.target.value })} /></Field>
            <NamesEditor value={f.names} onChange={(names) => set({ names })} />
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Field label={t("admin.common.kind")}><Select value={f.kind} onChange={(e) => set({ kind: e.target.value as QBaseIn["kind"] })}>{SOURCE_KINDS.map((k) => <option key={k} value={k}>{en("sourceKind", k)}</option>)}</Select></Field>
              <Field label={t("admin.common.year")}><Input type="number" value={f.year ?? ""} onChange={(e) => set({ year: e.target.value ? Number(e.target.value) : null })} /></Field>
              <Field label={t("admin.common.position")}><Input type="number" value={f.position ?? 0} onChange={(e) => set({ position: Number(e.target.value) })} /></Field>
            </div>
            <Field label={t("admin.sources.provenance")}><Input value={f.provenance ?? ""} onChange={(e) => set({ provenance: e.target.value })} /></Field>
            <Field label={t("admin.sources.licenseNote")}><Input value={f.license_note ?? ""} onChange={(e) => set({ license_note: e.target.value })} /></Field>
            <Check checked={f.active ?? true} onChange={(active) => set({ active })} label={t("admin.common.active")} />
          </div>
        )}
      </Drawer>
      {confirmNode}
    </>
  );
}
