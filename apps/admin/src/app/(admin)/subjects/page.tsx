"use client";
import { useT } from "@/lib/i18n";
import { useState } from "react";
import { catalog, qk, useAct, useSubjects, type Subject, type SubjectIn } from "@/lib/catalog";
import { fieldErrors } from "@/lib/util";
import { nm } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader } from "@/components/ui/controls";
import { Drawer } from "@/components/ui/overlay";
import { useConfirm } from "@/components/ui/confirm";
import { DataTable } from "@/components/ui/table";
import { NamesEditor, cleanNames } from "@/components/ui/names";

const blank: SubjectIn = { code: "", names: {}, weight: 1, active: true, position: 0 };

export default function SubjectsPage() {
  const t = useT();
  const [ask, confirmNode] = useConfirm();
  const q = useSubjects();
  const [edit, setEdit] = useState<{ id?: string; form: SubjectIn } | null>(null);
  const save = useAct(
    (e: { id?: string; form: SubjectIn }) => {
      const body = { ...e.form, names: cleanNames(e.form.names) };
      return e.id ? catalog.subjects.update(e.id, body) : catalog.subjects.create(body);
    },
    [qk.subjects],
    t("admin.common.saved"),
  );
  const del = useAct((id: string) => catalog.subjects.remove(id), [qk.subjects], t("admin.common.deleted"));
  const rows = [...(q.data ?? [])].sort((a, b) => a.position - b.position);
  const f = edit?.form;
  const fe = fieldErrors(save.error);
  const set = (p: Partial<SubjectIn>) => setEdit((e) => e && { ...e, form: { ...e.form, ...p } });
  const open = (s: Subject) => setEdit({ id: s.id, form: { code: s.code, names: s.names, weight: s.weight, active: s.active, position: s.position } });

  return (
    <>
      <PageHeader title={t("admin.common.subjects")} sub={t("admin.subjects.weightDrivesThePredicted")} actions={<Btn variant="primary" onClick={() => setEdit({ form: { ...blank, position: rows.length } })}>{t("admin.subjects.newSubject")}</Btn>} />
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={rows} loading={q.isLoading} error={q.error} rowKey={(r) => r.id} onRow={open}
          cols={[
            { key: "pos", head: "#", cell: (r) => r.position, className: "w-12" },
            { key: "code", head: t("admin.common.code"), cell: (r) => <code>{r.code}</code> },
            { key: "name", head: t("admin.common.name"), cell: (r) => nm(r.names) },
            { key: "w", head: t("admin.common.weight"), cell: (r) => r.weight },
            { key: "act", head: t("admin.common.state"), cell: (r) => <Badge tone={r.active ? "green" : "gray"}>{r.active ? t("admin.common.active") : t("admin.topics.inactive")}</Badge> },
          ]} />
      </div>
      <Drawer open={!!edit} onClose={() => setEdit(null)} width="max-w-lg" title={edit?.id ? t("admin.subjects.editSubject") : t("admin.subjects.newSubject")}
        footer={<>
          {edit?.id && <Btn variant="danger" className="mr-auto" onClick={() => { const saved = rows.find((r) => r.id === edit.id); ask({ title: t("admin.subjects.deleteThisSubject"), name: saved ? nm(saved.names) || saved.code : edit.form.code, danger: true, confirmLabel: t("admin.common.delete") }, () => del.mutate(edit.id!, { onSuccess: () => setEdit(null) })); }}>{t("admin.common.delete")}</Btn>}
          <Btn onClick={() => setEdit(null)}>{t("admin.common.cancel")}</Btn>
          <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(edit!, { onSuccess: () => setEdit(null) })}>{t("admin.common.save")}</Btn>
        </>}>
        {f && (
          <div className="space-y-3">
            <Field label={t("admin.common.code")} hint={t("admin.subjects.lowercaseDigitsOr")} error={fe.code}><Input value={f.code} onChange={(e) => set({ code: e.target.value })} /></Field>
            <NamesEditor value={f.names} onChange={(names) => set({ names })} error={fe.names} />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field label={t("admin.common.weight")} error={fe.weight}><Input type="number" step="0.1" min={0} value={f.weight} onChange={(e) => set({ weight: Number(e.target.value) })} /></Field>
              <Field label={t("admin.common.position")} error={fe.position}><Input type="number" value={f.position ?? 0} onChange={(e) => set({ position: Number(e.target.value) })} /></Field>
            </div>
            <Check checked={f.active} onChange={(active) => set({ active })} label={t("admin.common.active")} />
          </div>
        )}
      </Drawer>
      {confirmNode}
    </>
  );
}
