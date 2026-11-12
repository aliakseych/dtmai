"use client";
import { Icon } from "@dtmai/ui";
import { useT } from "@/lib/i18n";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { catalog, qk, useAct, useSubjects, useTopics, useTypes, type LessonIn, type LessonT, type PathT, type UnitT } from "@/lib/catalog";
import { fieldErrors, nm } from "@/lib/util";
import { Badge, Btn, Check, Empty, Field, Input, PageHeader, Select, StatusBadge, Toolbar } from "@/components/ui/controls";
import { Drawer } from "@/components/ui/overlay";
import { useConfirm } from "@/components/ui/confirm";
import { NamesEditor, cleanNames } from "@/components/ui/names";
import { MultiPick } from "@/components/ui/multipick";
import { LangInput } from "@/components/ui/lang";
import { TheoryEditor } from "@/components/lessons/TheoryEditor";

export default function PathsPage() {
  const t = useT();
  const [ask, confirmNode] = useConfirm();
  const subjects = useSubjects();
  const [subjectId, setSubjectId] = useState("");
  const sid = subjectId || subjects.data?.[0]?.id;
  const paths = useQuery({ queryKey: qk.paths(sid ?? ""), queryFn: () => catalog.paths.list(sid!), enabled: !!sid });
  const [pathId, setPathId] = useState("");
  const path: PathT | undefined = paths.data?.find((p) => p.id === pathId) ?? paths.data?.[0];
  const units = useQuery({ queryKey: qk.units(path?.id ?? ""), queryFn: () => catalog.units.list(path!.id), enabled: !!path });
  // Pool per lesson: verified questions matching the lesson selectors vs what it needs (server-computed).
  const gate = useQuery({ queryKey: ["launch-gate", sid], queryFn: () => catalog.launchGate(sid!), enabled: !!sid, staleTime: 5_000 });
  const gateBy = new Map(gate.data?.map((g) => [g.lesson_id, g]));

  const [pathForm, setPathForm] = useState<{ language: string; names: Record<string, string> } | null>(null);
  const [unitEdit, setUnitEdit] = useState<{ id?: string; names: Record<string, string> } | null>(null);
  const [lessonEdit, setLessonEdit] = useState<{ id?: string; form: LessonIn } | null>(null);

  const invPaths = [qk.paths(sid ?? "")];
  const invUnits = [qk.units(path?.id ?? ""), ["launch-gate", sid]] as const;
  const createPath = useAct(() => catalog.paths.create({ subject_id: sid!, language: pathForm!.language, names: cleanNames(pathForm!.names), position: paths.data?.length ?? 0 }), invPaths, t("admin.paths.pathCreated"));
  const toggle = useAct((p: PathT) => (p.status === "published" ? catalog.paths.unpublish(p.id) : catalog.paths.publish(p.id)), invPaths, t("admin.common.updated"));
  const pe = fieldErrors(createPath.error);
  const delPath = useAct((id: string) => catalog.paths.remove(id), invPaths, t("admin.common.deleted"));
  const saveUnit = useAct((e: { id?: string; names: Record<string, string> }) => e.id ? catalog.units.update(e.id, { names: cleanNames(e.names) }) : catalog.units.create({ path_id: path!.id, names: cleanNames(e.names), position: units.data?.length ?? 0 }), invUnits, t("admin.common.saved"));
  const ue = fieldErrors(saveUnit.error);
  const delUnit = useAct((id: string) => catalog.units.remove(id), invUnits, t("admin.common.deleted"));
  const moveUnit = useAct(async (a: { id: string; dir: -1 | 1 }) => {
    const ids = (units.data ?? []).map((u) => u.id);
    const i = ids.indexOf(a.id), j = i + a.dir;
    if (j < 0 || j >= ids.length) return;
    [ids[i], ids[j]] = [ids[j]!, ids[i]!];
    await catalog.units.reorder(path!.id, ids);
  }, invUnits);

  return (
    <>
      <PageHeader title={t("admin.paths.pathsLessons")} sub={t("admin.paths.pathUnitsLessonsLessons")} />
      <Toolbar>
        <Field label={t("admin.common.subject")}><Select value={sid ?? ""} onChange={(e) => { setSubjectId(e.target.value); setPathId(""); }}>{subjects.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select></Field>
        <Field label={t("admin.paths.pathLanguage")}><Select value={path?.id ?? ""} onChange={(e) => setPathId(e.target.value)}>{paths.data?.map((p) => <option key={p.id} value={p.id}>{p.language} · {nm(p.names)}</option>)}</Select></Field>
        <Btn onClick={() => setPathForm({ language: "uz", names: {} })} disabled={!sid}>{t("admin.paths.newPath")}</Btn>
        {path && <>
          <Btn variant={path.status === "published" ? "default" : "primary"} onClick={() => toggle.mutate(path)}>{path.status === "published" ? t("admin.paths.unpublish") : t("admin.common.publish")}</Btn>
          <Btn variant="danger" onClick={() => ask({ title: t("admin.paths.deletePathAndAll"), name: nm(path.names), danger: true, confirmLabel: t("admin.common.delete") }, () => delPath.mutate(path.id))}>{t("admin.common.delete")}</Btn>
          <StatusBadge status={path.status} />
        </>}
      </Toolbar>
      <div className="min-h-0 flex-1 space-y-3 overflow-auto p-4">
        {!path && <Empty>{paths.isLoading ? t("admin.common.loading") : t("admin.paths.noPathForThis")}</Empty>}
        {path && (
          <Btn variant="primary" onClick={() => setUnitEdit({ names: {} })}>{t("admin.paths.addUnit")}</Btn>
        )}
        {units.data?.map((u, i) => (
          <UnitCard key={u.id} unit={u} gateBy={gateBy} subjectId={sid!} onEdit={() => setUnitEdit({ id: u.id, names: u.names })} onDelete={() => ask({ title: t("admin.paths.deleteUnit"), name: nm(u.names), danger: true, confirmLabel: t("admin.common.delete") }, () => delUnit.mutate(u.id))}
            onUp={i > 0 ? () => moveUnit.mutate({ id: u.id, dir: -1 }) : undefined} onDown={i < units.data.length - 1 ? () => moveUnit.mutate({ id: u.id, dir: 1 }) : undefined}
            onLesson={(l, unitId) => setLessonEdit(l ? { id: l.id, form: { unit_id: l.unit_id, names: l.names, topic_ids: l.topic_ids, type_ids: l.type_ids, question_count: l.question_count, legendary: l.legendary, theory: l.theory, position: l.position } } : { form: { unit_id: unitId, names: {}, topic_ids: [], type_ids: [], question_count: 10, legendary: false, theory: [], position: 99 } })} />
        ))}
      </div>

      <Drawer open={!!pathForm} onClose={() => setPathForm(null)} width="max-w-lg" title={t("admin.paths.newPath")} footer={<><Btn onClick={() => setPathForm(null)}>{t("admin.common.cancel")}</Btn><Btn variant="primary" onClick={() => createPath.mutate(undefined, { onSuccess: () => setPathForm(null) })}>{t("admin.common.create")}</Btn></>}>
        {pathForm && <div className="space-y-3">
          <Field label={t("admin.common.language")} error={pe.language}><LangInput value={pathForm.language} onChange={(language) => setPathForm({ ...pathForm, language })} /></Field>
          <NamesEditor value={pathForm.names} onChange={(names) => setPathForm({ ...pathForm, names })} error={pe.names} />
        </div>}
      </Drawer>
      <Drawer open={!!unitEdit} onClose={() => setUnitEdit(null)} width="max-w-lg" title={unitEdit?.id ? t("admin.paths.editUnit") : t("admin.paths.newUnit")} footer={<><Btn onClick={() => setUnitEdit(null)}>{t("admin.common.cancel")}</Btn><Btn variant="primary" onClick={() => saveUnit.mutate(unitEdit!, { onSuccess: () => setUnitEdit(null) })}>{t("admin.common.save")}</Btn></>}>
        {unitEdit && <NamesEditor value={unitEdit.names} onChange={(names) => setUnitEdit({ ...unitEdit, names })} error={ue.names} />}
      </Drawer>
      <LessonDrawer edit={lessonEdit} close={() => setLessonEdit(null)} setEdit={setLessonEdit} subjectId={sid} gateBy={gateBy} invalidate={invUnits} />
      {confirmNode}
    </>
  );
}

type Gate = Map<string, { pool: number; needed: number; visible: boolean }>;

function PoolBadge({ g }: { g?: { pool: number; needed: number; visible: boolean } }) {
  const t = useT();
  if (!g) return <Badge>{t("admin.paths.pool")}</Badge>;
  return <Badge tone={g.pool >= g.needed ? "green" : "red"}>{t("admin.paths.poolBadge", { pool: g.pool, needed: g.needed })}{g.visible ? "" : t("admin.paths.hidden")}</Badge>;
}

function UnitCard({ unit, gateBy, onEdit, onDelete, onUp, onDown, onLesson }: { unit: UnitT; gateBy: Gate; subjectId: string; onEdit: () => void; onDelete: () => void; onUp?: () => void; onDown?: () => void; onLesson: (l: LessonT | null, unitId: string) => void }) {
  const t = useT();
  const lessons = useQuery({ queryKey: qk.lessons(unit.id), queryFn: () => catalog.lessons.list(unit.id) });
  return (
    <section className="rounded-2xl border border-line bg-white">
      <header className="flex items-center gap-2 border-b border-line px-3 py-2">
        <h3 className="flex-1 text-sm">{nm(unit.names)}</h3>
        <Btn variant="ghost" disabled={!onUp} onClick={onUp} aria-label={t("admin.common.moveUp")}><Icon name="arrow-up" size={16} /></Btn>
        <Btn variant="ghost" disabled={!onDown} onClick={onDown} aria-label={t("admin.common.moveDown")}><Icon name="arrow-down" size={16} /></Btn>
        <Btn onClick={onEdit}>{t("admin.paths.rename")}</Btn>
        <Btn variant="danger" onClick={onDelete}>{t("admin.common.delete")}</Btn>
        <Btn variant="primary" onClick={() => onLesson(null, unit.id)}>{t("admin.paths.addLesson")}</Btn>
      </header>
      {lessons.data?.length === 0 && <Empty>{t("admin.paths.noLessons")}</Empty>}
      {lessons.data?.map((l) => (
        <button key={l.id} type="button" onClick={() => onLesson(l, unit.id)} className="flex w-full items-center gap-3 border-b border-line px-3 py-1.5 text-left last:border-0 hover:bg-blue-soft/50">
          <span className="flex-1">{nm(l.names)}</span>
          {l.legendary && <Badge tone="gold">{t("admin.paths.legendary2")}</Badge>}
          {l.theory.length > 0 && <Badge>{t("admin.paths.theoryN", { n: l.theory.length })}</Badge>}
          <span className="text-xs text-ink-soft">{t("admin.paths.lessonMeta", { q: l.question_count, topics: l.topic_ids.length, types: l.type_ids.length })}</span>
          <PoolBadge g={gateBy.get(l.id)} />
        </button>
      ))}
    </section>
  );
}

function LessonDrawer({ edit, close, setEdit, subjectId, gateBy, invalidate }: { edit: { id?: string; form: LessonIn } | null; close: () => void; setEdit: (e: { id?: string; form: LessonIn } | null) => void; subjectId?: string; gateBy: Gate; invalidate: readonly (readonly unknown[])[] }) {
  const t = useT();
  const [ask, confirmNode] = useConfirm();
  const topics = useTopics(subjectId);
  const types = useTypes();
  const unitId = edit?.form.unit_id ?? "";
  const inv = [...invalidate, qk.lessons(unitId)];
  const save = useAct((e: { id?: string; form: LessonIn }) => {
    const body = { ...e.form, names: cleanNames(e.form.names) };
    return e.id ? catalog.lessons.update(e.id, body) : catalog.lessons.create(body);
  }, inv, t("admin.common.saved"));
  const del = useAct((id: string) => catalog.lessons.remove(id), inv, t("admin.common.deleted"));
  const f = edit?.form;
  const fe = fieldErrors(save.error);
  const set = (p: Partial<LessonIn>) => edit && setEdit({ ...edit, form: { ...edit.form, ...p } });
  return (
    <><Drawer open={!!edit} onClose={close} width="max-w-3xl" title={edit?.id ? t("admin.paths.editLesson") : t("admin.paths.newLesson")}
      footer={<>
        {edit?.id && <Btn variant="danger" className="mr-auto" onClick={() => ask({ title: t("admin.paths.deleteLesson"), name: nm(f?.names), danger: true, confirmLabel: t("admin.common.delete") }, () => del.mutate(edit.id!, { onSuccess: close }))}>{t("admin.common.delete")}</Btn>}
        <Btn onClick={close}>{t("admin.common.cancel")}</Btn>
        <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(edit!, { onSuccess: close })}>{t("admin.common.save")}</Btn>
      </>}>
      {f && edit && (
        <div className="space-y-3">
          <NamesEditor value={f.names} onChange={(names) => set({ names })} error={fe.names} />
          <Field label={t("admin.common.topics")} hint={t("admin.paths.emptyAllTopicsOf")} error={fe.topic_ids}><MultiPick options={(topics.data ?? []).map((t) => ({ id: t.id, label: nm(t.names) }))} value={f.topic_ids ?? []} onChange={(topic_ids) => set({ topic_ids })} /></Field>
          <Field label={t("admin.common.questionTypes")} hint={t("admin.paths.emptyAllTypes")} error={fe.type_ids}><MultiPick options={(types.data ?? []).map((t) => ({ id: t.id, label: `${nm(t.names)} · ${t.kind}` }))} value={f.type_ids ?? []} onChange={(type_ids) => set({ type_ids })} /></Field>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label={t("admin.paths.questionsPerRun1")} error={fe.question_count}><Input type="number" min={1} max={100} value={f.question_count ?? 10} onChange={(e) => set({ question_count: Number(e.target.value) })} /></Field>
            <div className="flex items-end gap-3"><Check checked={f.legendary ?? false} onChange={(legendary) => set({ legendary })} label={t("admin.paths.legendary")} />{edit.id && <PoolBadge g={gateBy.get(edit.id)} />}</div>
          </div>
          <p className="text-xs text-ink-soft">{t("admin.paths.thePoolBadgeIs")}</p>
          <TheoryEditor value={f.theory ?? []} onChange={(theory) => set({ theory })} />
          {fe.theory && <p role="alert" className="text-xs font-bold text-red-deep">{fe.theory}</p>}
        </div>
      )}
    </Drawer>{confirmNode}</>
  );
}
