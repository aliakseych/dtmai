"use client";
import { useState } from "react";
import { catalog, qk, useAct, useTypes, type QType, type QTypeIn } from "@/lib/catalog";
import { QUESTION_KINDS, nm } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader, Select, Textarea } from "@/components/ui/controls";
import { Drawer } from "@/components/ui/overlay";
import { DataTable } from "@/components/ui/table";
import { NamesEditor, cleanNames } from "@/components/ui/names";
import { JsonEditor } from "@/components/ui/json";

const blank: QTypeIn = { code: "", kind: "single_choice", names: {}, config: {}, generation_prompt: "", rules: {}, active: true, position: 0 };
const CONFIG_HINT = 'Keys: option_count (2–10, choice kinds only), label_scheme ("latin"|"cyrillic"|"numeric"|"none"), image_stem (bool), option_style, rules (string[]). The API validates on save.';

export default function QuestionTypesPage() {
  const q = useTypes();
  const [edit, setEdit] = useState<{ id?: string; form: QTypeIn } | null>(null);
  const save = useAct(
    (e: { id?: string; form: QTypeIn }) => {
      const body = { ...e.form, names: cleanNames(e.form.names) };
      return e.id ? catalog.types.update(e.id, body) : catalog.types.create(body);
    },
    [qk.types],
    "Saved",
  );
  const del = useAct((id: string) => catalog.types.remove(id), [qk.types], "Deleted");
  const f = edit?.form;
  const set = (p: Partial<QTypeIn>) => setEdit((e) => e && { ...e, form: { ...e.form, ...p } });
  const open = (t: QType) => setEdit({ id: t.id, form: { code: t.code, kind: t.kind as QTypeIn["kind"], names: t.names, config: t.config, generation_prompt: t.generation_prompt ?? "", rules: t.rules ?? {}, active: t.active, position: t.position } });

  return (
    <>
      <PageHeader title="Question types" sub="A type = kind (closed set) + dynamic config + generation prompt." actions={<Btn variant="primary" onClick={() => setEdit({ form: { ...blank, position: q.data?.length ?? 0 } })}>New type</Btn>} />
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(r) => r.id} onRow={open}
          cols={[
            { key: "code", head: "Code", cell: (r) => <code>{r.code}</code> },
            { key: "name", head: "Name", cell: (r) => nm(r.names) },
            { key: "kind", head: "Kind", cell: (r) => <Badge tone="blue">{r.kind}</Badge> },
            { key: "cfg", head: "Config", cell: (r) => <code className="text-xs text-ink-soft">{JSON.stringify(r.config)}</code> },
            { key: "act", head: "State", cell: (r) => <Badge tone={r.active ? "green" : "gray"}>{r.active ? "active" : "inactive"}</Badge> },
          ]} />
      </div>
      <Drawer open={!!edit} onClose={() => setEdit(null)} title={edit?.id ? "Edit type" : "New type"}
        footer={<>
          {edit?.id && <Btn variant="danger" className="mr-auto" onClick={() => confirm("Delete this type?") && del.mutate(edit.id!, { onSuccess: () => setEdit(null) })}>Delete</Btn>}
          <Btn onClick={() => setEdit(null)}>Cancel</Btn>
          <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(edit!, { onSuccess: () => setEdit(null) })}>Save</Btn>
        </>}>
        {f && (
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <Field label="Code"><Input value={f.code} onChange={(e) => set({ code: e.target.value })} /></Field>
              <Field label="Kind"><Select value={f.kind} onChange={(e) => set({ kind: e.target.value as QTypeIn["kind"] })}>{QUESTION_KINDS.map((k) => <option key={k}>{k}</option>)}</Select></Field>
              <Field label="Position"><Input type="number" value={f.position ?? 0} onChange={(e) => set({ position: Number(e.target.value) })} /></Field>
            </div>
            <NamesEditor value={f.names} onChange={(names) => set({ names })} />
            <Field label="Config (JSON)"><JsonEditor value={f.config} onChange={(config) => set({ config: config as QTypeIn["config"] })} hint={CONFIG_HINT} /></Field>
            <Field label="Generation prompt" hint="Template used by AI generation runs for this type."><Textarea rows={6} value={f.generation_prompt ?? ""} onChange={(e) => set({ generation_prompt: e.target.value })} /></Field>
            <Field label="Rules (JSON)"><JsonEditor rows={4} value={f.rules ?? {}} onChange={(v) => set({ rules: v as QTypeIn["rules"] })} /></Field>
            <Check checked={f.active ?? true} onChange={(active) => set({ active })} label="Active" />
          </div>
        )}
      </Drawer>
    </>
  );
}
