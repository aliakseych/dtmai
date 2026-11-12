"use client";
import { useEnum, useT } from "@/lib/i18n";
import { useState } from "react";
import { catalog, qk, useAct, useTypes, type QType, type QTypeIn } from "@/lib/catalog";
import { QUESTION_KINDS, fieldErrors, nm } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader, Select, Textarea } from "@/components/ui/controls";
import { Drawer } from "@/components/ui/overlay";
import { useConfirm } from "@/components/ui/confirm";
import { DataTable } from "@/components/ui/table";
import { NamesEditor, cleanNames } from "@/components/ui/names";
import { JsonEditor } from "@/components/ui/json";

const blank: QTypeIn = { code: "", kind: "single_choice", names: {}, config: {}, generation_prompt: "", rules: {}, active: true, position: 0 };
const CONFIG_HINT = "admin.questionTypes.configHint";

export default function QuestionTypesPage() {
  const t = useT();
  const en = useEnum();
  const [ask, confirmNode] = useConfirm();
  const q = useTypes();
  const [edit, setEdit] = useState<{ id?: string; form: QTypeIn } | null>(null);
  const save = useAct(
    (e: { id?: string; form: QTypeIn }) => {
      const body = { ...e.form, names: cleanNames(e.form.names) };
      return e.id ? catalog.types.update(e.id, body) : catalog.types.create(body);
    },
    [qk.types],
    t("admin.common.saved"),
  );
  const del = useAct((id: string) => catalog.types.remove(id), [qk.types], t("admin.common.deleted"));
  const f = edit?.form;
  const fe = fieldErrors(save.error);
  const set = (p: Partial<QTypeIn>) => setEdit((e) => e && { ...e, form: { ...e.form, ...p } });
  const open = (t: QType) => setEdit({ id: t.id, form: { code: t.code, kind: t.kind as QTypeIn["kind"], names: t.names, config: t.config, generation_prompt: t.generation_prompt ?? "", rules: t.rules ?? {}, active: t.active, position: t.position } });

  return (
    <>
      <PageHeader title={t("admin.common.questionTypes")} sub={t("admin.questionTypes.aTypeKindClosed")} actions={<Btn variant="primary" onClick={() => setEdit({ form: { ...blank, position: q.data?.length ?? 0 } })}>{t("admin.questionTypes.newType")}</Btn>} />
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(r) => r.id} onRow={open}
          cols={[
            { key: "code", head: t("admin.common.code"), cell: (r) => <code>{r.code}</code> },
            { key: "name", head: t("admin.common.name"), cell: (r) => nm(r.names) },
            { key: "kind", head: t("admin.common.kind"), cell: (r) => <Badge tone="blue">{en("kind", r.kind)}</Badge> },
            { key: "cfg", head: t("admin.questionTypes.config"), cell: (r) => <code className="text-xs text-ink-soft">{JSON.stringify(r.config)}</code> },
            { key: "act", head: t("admin.common.state"), cell: (r) => <Badge tone={r.active ? "green" : "gray"}>{r.active ? t("admin.common.active") : t("admin.topics.inactive")}</Badge> },
          ]} />
      </div>
      <Drawer open={!!edit} onClose={() => setEdit(null)} title={edit?.id ? t("admin.questionTypes.editType") : t("admin.questionTypes.newType")}
        footer={<>
          {edit?.id && <Btn variant="danger" className="mr-auto" onClick={() => ask({ title: t("admin.questionTypes.deleteThisType"), name: nm(edit.form.names) || edit.form.code, danger: true, confirmLabel: t("admin.common.delete") }, () => del.mutate(edit.id!, { onSuccess: () => setEdit(null) }))}>{t("admin.common.delete")}</Btn>}
          <Btn onClick={() => setEdit(null)}>{t("admin.common.cancel")}</Btn>
          <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(edit!, { onSuccess: () => setEdit(null) })}>{t("admin.common.save")}</Btn>
        </>}>
        {f && (
          <div className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Field label={t("admin.common.code")} error={fe.code}><Input value={f.code} onChange={(e) => set({ code: e.target.value })} /></Field>
              <Field label={t("admin.common.kind")} error={fe.kind}><Select value={f.kind} onChange={(e) => set({ kind: e.target.value as QTypeIn["kind"] })}>{QUESTION_KINDS.map((k) => <option key={k} value={k}>{en("kind", k)}</option>)}</Select></Field>
              <Field label={t("admin.common.position")} error={fe.position}><Input type="number" value={f.position ?? 0} onChange={(e) => set({ position: Number(e.target.value) })} /></Field>
            </div>
            <NamesEditor value={f.names} onChange={(names) => set({ names })} error={fe.names} />
            <Field label={t("admin.questionTypes.configJson")} error={fe.config}><JsonEditor value={f.config} onChange={(config) => set({ config: config as QTypeIn["config"] })} hint={t(CONFIG_HINT)} /></Field>
            <Field label={t("admin.questionTypes.generationPrompt")} hint={t("admin.questionTypes.templateUsedByAi")} error={fe.generation_prompt}><Textarea rows={6} value={f.generation_prompt ?? ""} onChange={(e) => set({ generation_prompt: e.target.value })} /></Field>
            <Field label={t("admin.questionTypes.rulesJson")} error={fe.rules}><JsonEditor rows={4} value={f.rules ?? {}} onChange={(v) => set({ rules: v as QTypeIn["rules"] })} /></Field>
            <Check checked={f.active ?? true} onChange={(active) => set({ active })} label={t("admin.common.active")} />
          </div>
        )}
      </Drawer>
      {confirmNode}
    </>
  );
}
