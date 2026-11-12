"use client";
import { useEnum, useT } from "@/lib/i18n";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { catalog, qk, useAct, useBases, useSubjects, useTopics, useTypes, type Blueprint, type BlueprintIn } from "@/lib/catalog";
import { BLUEPRINT_KINDS, nm } from "@/lib/util";
import { Badge, Btn, Field, Input, PageHeader, Select, StatusBadge } from "@/components/ui/controls";
import { Drawer } from "@/components/ui/overlay";
import { useConfirm } from "@/components/ui/confirm";
import { DataTable } from "@/components/ui/table";
import { NamesEditor, cleanNames } from "@/components/ui/names";
import { MultiPick } from "@/components/ui/multipick";

interface Section { subject_id: string; topic_ids: string[]; type_ids: string[]; count: number; weight: number; question_ids?: string[] }
const blankSection = (subject_id: string): Section => ({ subject_id, topic_ids: [], type_ids: [], count: 10, weight: 1 });
const blank: BlueprintIn = { code: "", names: {}, kind: "generated", sections: [], duration_min: 60, source_id: null };

export default function BlueprintsPage() {
  const t = useT();
  const en = useEnum();
  const [ask, confirmNode] = useConfirm();
  const q = useQuery({ queryKey: qk.blueprints, queryFn: catalog.blueprints.list });
  const [edit, setEdit] = useState<{ id?: string; status?: string; version?: number; form: BlueprintIn; base?: string } | null>(null);
  const inv = [qk.blueprints];
  const save = useAct((e: NonNullable<typeof edit>) => {
    const body = { ...e.form, names: cleanNames(e.form.names) };
    return e.id ? catalog.blueprints.update(e.id, body) : catalog.blueprints.create(body);
  }, inv, t("admin.common.saved"));
  const publish = useAct((id: string) => catalog.blueprints.publish(id), inv, t("admin.common.published"));
  const clone = useAct((id: string) => catalog.blueprints.clone(id), inv, t("admin.blueprints.clonedAsDraft"));
  const del = useAct((id: string) => catalog.blueprints.remove(id), inv, t("admin.common.deleted"));
  const locked = edit?.status === "published";
  const dirty = !!edit?.id && JSON.stringify(edit.form) !== edit.base;
  const f = edit?.form;
  const set = (p: Partial<BlueprintIn>) => setEdit((e) => e && { ...e, form: { ...e.form, ...p } });
  const sections = (f?.sections ?? []) as unknown as Section[];
  const setSections = (s: Section[]) => set({ sections: s as unknown as BlueprintIn["sections"] });
  const bases = useBases();
  const subjects = useSubjects();
  const open = (b: Blueprint) => { const form: BlueprintIn = { code: b.code, names: b.names, kind: b.kind as BlueprintIn["kind"], sections: b.sections, duration_min: b.duration_min, source_id: b.source_id ?? null }; setEdit({ id: b.id, status: b.status, version: b.version, form, base: JSON.stringify(form) }); };

  return (
    <>
      <PageHeader title={t("admin.blueprints.mockBlueprints")} sub={t("admin.blueprints.draftPublishCreatesThe")} actions={<Btn variant="primary" onClick={() => setEdit({ form: blank })}>{t("admin.blueprints.newBlueprint")}</Btn>} />
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(r) => r.id} onRow={open} empty={<div className="space-y-2"><p>{t("admin.blueprints.emptyConsequence")}</p><Btn variant="primary" onClick={() => setEdit({ form: blank })}>{t("admin.blueprints.newBlueprint")}</Btn></div>}
          cols={[
            { key: "code", head: t("admin.common.code"), cell: (r) => <code>{r.code}</code> },
            { key: "name", head: t("admin.common.name"), cell: (r) => nm(r.names) },
            { key: "kind", head: t("admin.common.kind"), cell: (r) => <Badge tone="blue">{en("blueprintKind", r.kind)}</Badge> },
            { key: "v", head: t("admin.blueprints.version"), cell: (r) => (r.status === "published" ? `v${r.version}` : "—") },
            { key: "st", head: t("admin.common.status"), cell: (r) => <StatusBadge status={r.status} /> },
            { key: "d", head: t("admin.common.min"), cell: (r) => r.duration_min },
            { key: "s", head: t("admin.common.sections"), cell: (r) => r.sections.length },
          ]} />
      </div>
      <Drawer open={!!edit} onClose={() => setEdit(null)} title={`${edit?.id ? t("admin.blueprints.blueprint") : t("admin.blueprints.newBlueprint")}${edit?.status ? ` · ${t(`admin.status.${edit.status}`)}` : ""}`}
        footer={<>
          {edit?.id && !locked && <Btn variant="danger" className="mr-auto" onClick={() => ask({ title: t("admin.blueprints.deleteBlueprint"), name: nm(edit.form.names), danger: true, confirmLabel: t("admin.common.delete") }, () => del.mutate(edit.id!, { onSuccess: () => setEdit(null) }))}>{t("admin.common.delete")}</Btn>}
          <Btn onClick={() => setEdit(null)}>{t("admin.common.close")}</Btn>
          {edit?.id && locked && <Btn onClick={() => clone.mutate(edit.id!, { onSuccess: () => setEdit(null) })}>{t("admin.blueprints.cloneAsDraft")}</Btn>}
          {edit?.id && !locked && <Btn disabled={dirty || publish.isPending} title={dirty ? t("admin.blueprints.saveBeforePublish") : undefined} onClick={() => ask({ title: t("admin.blueprints.publishThisDraftAs"), name: nm(edit.form.names), body: <p className="text-sm text-ink-soft">{t("admin.blueprints.publishIrreversible")}</p>, confirmLabel: t("admin.common.publish"), danger: true }, () => publish.mutate(edit.id!, { onSuccess: () => setEdit(null) }))}>{t("admin.common.publish")}</Btn>}
          {!locked && <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(edit!, { onSuccess: () => setEdit(null) })}>{t("admin.common.save")}</Btn>}
        </>}>
        {f && (
          <fieldset disabled={locked} className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <Field label={t("admin.common.code")}><Input value={f.code} onChange={(e) => set({ code: e.target.value })} /></Field>
              <Field label={t("admin.common.kind")}><Select value={f.kind} onChange={(e) => set({ kind: e.target.value as BlueprintIn["kind"] })}>{BLUEPRINT_KINDS.map((k) => <option key={k} value={k}>{en("blueprintKind", k)}</option>)}</Select></Field>
              <Field label={t("admin.blueprints.durationMin")}><Input type="number" min={1} value={f.duration_min} onChange={(e) => set({ duration_min: Number(e.target.value) })} /></Field>
              <Field label={t("admin.common.source")}><Select value={f.source_id ?? ""} onChange={(e) => set({ source_id: e.target.value || null })}><option value="">—</option>{bases.data?.map((b) => <option key={b.id} value={b.id}>{nm(b.names)}</option>)}</Select></Field>
            </div>
            <NamesEditor value={f.names} onChange={(names) => set({ names })} />
            <div className="flex items-center justify-between"><h3 className="text-sm">{t("admin.blueprints.sectionsCount", { n: sections.length })}</h3>
              <Btn onClick={() => subjects.data?.[0] && setSections([...sections, blankSection(subjects.data[0].id)])}>{t("admin.blueprints.addSection")}</Btn></div>
            {sections.map((s, i) => (
              <SectionEditor key={i} s={s} onChange={(n) => setSections(sections.map((x, j) => (j === i ? n : x)))} onRemove={() => setSections(sections.filter((_, j) => j !== i))} />
            ))}
            <p className="text-xs text-ink-soft">{t("admin.blueprints.totalHint", { n: sections.reduce((a, s) => a + (s.count || 0), 0) })} <code>{t("admin.blueprints.questionIds")}</code> {t("admin.blueprints.countMustMatch")}</p>
            {dirty && !locked && <p className="text-xs font-bold text-orange">{t("admin.blueprints.saveBeforePublish")}</p>}
          </fieldset>
        )}
      </Drawer>
      {confirmNode}
    </>
  );
}

function SectionEditor({ s, onChange, onRemove }: { s: Section; onChange: (s: Section) => void; onRemove: () => void }) {
  const t = useT();
  const subjects = useSubjects();
  const topics = useTopics(s.subject_id);
  const types = useTypes();
  return (
    <div className="space-y-2 rounded-xl border border-line p-2">
      <div className="grid grid-cols-2 sm:grid-cols-[1fr_6rem_6rem_auto] items-end gap-2">
        <Field label={t("admin.common.subject")}><Select value={s.subject_id} onChange={(e) => onChange({ ...s, subject_id: e.target.value, topic_ids: [] })}>{subjects.data?.map((x) => <option key={x.id} value={x.id}>{nm(x.names)}</option>)}</Select></Field>
        <Field label={t("admin.common.count")}><Input type="number" min={1} value={s.count} onChange={(e) => onChange({ ...s, count: Number(e.target.value) })} /></Field>
        <Field label={t("admin.common.weight")}><Input type="number" step="0.1" min={0} value={s.weight} onChange={(e) => onChange({ ...s, weight: Number(e.target.value) })} /></Field>
        <Btn variant="danger" onClick={onRemove}>{t("admin.common.remove")}</Btn>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <Field label={t("admin.common.topics")}><MultiPick options={(topics.data ?? []).map((t) => ({ id: t.id, label: nm(t.names) }))} value={s.topic_ids} onChange={(topic_ids) => onChange({ ...s, topic_ids })} /></Field>
        <Field label={t("admin.blueprints.types")}><MultiPick options={(types.data ?? []).map((t) => ({ id: t.id, label: nm(t.names) }))} value={s.type_ids} onChange={(type_ids) => onChange({ ...s, type_ids })} /></Field>
      </div>
      {s.question_ids && <p className="text-xs text-ink-soft">{t("admin.blueprints.pinned", { n: s.question_ids.length })}</p>}
    </div>
  );
}
