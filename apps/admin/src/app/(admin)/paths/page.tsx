"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { catalog, qk, useAct, useSubjects, useTopics, useTypes, type LessonIn, type LessonT, type PathT, type UnitT } from "@/lib/catalog";
import { nm } from "@/lib/util";
import { Badge, Btn, Check, Empty, Field, Input, PageHeader, Select, StatusBadge, Toolbar } from "@/components/ui/controls";
import { Drawer } from "@/components/ui/overlay";
import { NamesEditor, cleanNames } from "@/components/ui/names";
import { MultiPick } from "@/components/ui/multipick";
import { LangInput } from "@/components/ui/lang";
import { TheoryEditor } from "@/components/lessons/TheoryEditor";

export default function PathsPage() {
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
  const createPath = useAct(() => catalog.paths.create({ subject_id: sid!, language: pathForm!.language, names: cleanNames(pathForm!.names), position: paths.data?.length ?? 0 }), invPaths, "Path created");
  const toggle = useAct((p: PathT) => (p.status === "published" ? catalog.paths.unpublish(p.id) : catalog.paths.publish(p.id)), invPaths, "Updated");
  const delPath = useAct((id: string) => catalog.paths.remove(id), invPaths, "Deleted");
  const saveUnit = useAct((e: { id?: string; names: Record<string, string> }) => e.id ? catalog.units.update(e.id, { names: cleanNames(e.names) }) : catalog.units.create({ path_id: path!.id, names: cleanNames(e.names), position: units.data?.length ?? 0 }), invUnits, "Saved");
  const delUnit = useAct((id: string) => catalog.units.remove(id), invUnits, "Deleted");
  const moveUnit = useAct(async (a: { id: string; dir: -1 | 1 }) => {
    const ids = (units.data ?? []).map((u) => u.id);
    const i = ids.indexOf(a.id), j = i + a.dir;
    if (j < 0 || j >= ids.length) return;
    [ids[i], ids[j]] = [ids[j]!, ids[i]!];
    await catalog.units.reorder(path!.id, ids);
  }, invUnits);

  return (
    <>
      <PageHeader title="Paths & lessons" sub="Path → units → lessons. Lessons draw from the verified pool by topic/type selectors." />
      <Toolbar>
        <Field label="Subject"><Select value={sid ?? ""} onChange={(e) => { setSubjectId(e.target.value); setPathId(""); }}>{subjects.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select></Field>
        <Field label="Path (language)"><Select value={path?.id ?? ""} onChange={(e) => setPathId(e.target.value)}>{paths.data?.map((p) => <option key={p.id} value={p.id}>{p.language} · {nm(p.names)}</option>)}</Select></Field>
        <Btn onClick={() => setPathForm({ language: "uz", names: {} })} disabled={!sid}>New path</Btn>
        {path && <>
          <Btn variant={path.status === "published" ? "default" : "primary"} onClick={() => toggle.mutate(path)}>{path.status === "published" ? "Unpublish" : "Publish"}</Btn>
          <Btn variant="danger" onClick={() => confirm("Delete path and all units/lessons?") && delPath.mutate(path.id)}>Delete</Btn>
          <StatusBadge status={path.status} />
        </>}
      </Toolbar>
      <div className="min-h-0 flex-1 space-y-3 overflow-auto p-4">
        {!path && <Empty>{paths.isLoading ? "Loading…" : "No path for this subject yet — create one."}</Empty>}
        {path && (
          <Btn variant="primary" onClick={() => setUnitEdit({ names: {} })}>Add unit</Btn>
        )}
        {units.data?.map((u, i) => (
          <UnitCard key={u.id} unit={u} gateBy={gateBy} subjectId={sid!} onEdit={() => setUnitEdit({ id: u.id, names: u.names })} onDelete={() => confirm("Delete unit?") && delUnit.mutate(u.id)}
            onUp={i > 0 ? () => moveUnit.mutate({ id: u.id, dir: -1 }) : undefined} onDown={i < units.data.length - 1 ? () => moveUnit.mutate({ id: u.id, dir: 1 }) : undefined}
            onLesson={(l, unitId) => setLessonEdit(l ? { id: l.id, form: { unit_id: l.unit_id, names: l.names, topic_ids: l.topic_ids, type_ids: l.type_ids, question_count: l.question_count, legendary: l.legendary, theory: l.theory, position: l.position } } : { form: { unit_id: unitId, names: {}, topic_ids: [], type_ids: [], question_count: 10, legendary: false, theory: [], position: 99 } })} />
        ))}
      </div>

      <Drawer open={!!pathForm} onClose={() => setPathForm(null)} width="max-w-lg" title="New path" footer={<><Btn onClick={() => setPathForm(null)}>Cancel</Btn><Btn variant="primary" onClick={() => createPath.mutate(undefined, { onSuccess: () => setPathForm(null) })}>Create</Btn></>}>
        {pathForm && <div className="space-y-3">
          <Field label="Language"><LangInput value={pathForm.language} onChange={(language) => setPathForm({ ...pathForm, language })} /></Field>
          <NamesEditor value={pathForm.names} onChange={(names) => setPathForm({ ...pathForm, names })} />
        </div>}
      </Drawer>
      <Drawer open={!!unitEdit} onClose={() => setUnitEdit(null)} width="max-w-lg" title={unitEdit?.id ? "Edit unit" : "New unit"} footer={<><Btn onClick={() => setUnitEdit(null)}>Cancel</Btn><Btn variant="primary" onClick={() => saveUnit.mutate(unitEdit!, { onSuccess: () => setUnitEdit(null) })}>Save</Btn></>}>
        {unitEdit && <NamesEditor value={unitEdit.names} onChange={(names) => setUnitEdit({ ...unitEdit, names })} />}
      </Drawer>
      <LessonDrawer edit={lessonEdit} close={() => setLessonEdit(null)} setEdit={setLessonEdit} subjectId={sid} gateBy={gateBy} invalidate={invUnits} />
    </>
  );
}

type Gate = Map<string, { pool: number; needed: number; visible: boolean }>;

function PoolBadge({ g }: { g?: { pool: number; needed: number; visible: boolean } }) {
  if (!g) return <Badge>pool —</Badge>;
  return <Badge tone={g.pool >= g.needed ? "green" : "red"}>pool {g.pool}/{g.needed}{g.visible ? "" : " · hidden"}</Badge>;
}

function UnitCard({ unit, gateBy, onEdit, onDelete, onUp, onDown, onLesson }: { unit: UnitT; gateBy: Gate; subjectId: string; onEdit: () => void; onDelete: () => void; onUp?: () => void; onDown?: () => void; onLesson: (l: LessonT | null, unitId: string) => void }) {
  const lessons = useQuery({ queryKey: qk.lessons(unit.id), queryFn: () => catalog.lessons.list(unit.id) });
  return (
    <section className="rounded-lg border border-line bg-white">
      <header className="flex items-center gap-2 border-b border-line px-3 py-2">
        <h3 className="flex-1 text-sm">{nm(unit.names)}</h3>
        <Btn variant="ghost" disabled={!onUp} onClick={onUp} aria-label="Move up">↑</Btn>
        <Btn variant="ghost" disabled={!onDown} onClick={onDown} aria-label="Move down">↓</Btn>
        <Btn onClick={onEdit}>Rename</Btn>
        <Btn variant="danger" onClick={onDelete}>Delete</Btn>
        <Btn variant="primary" onClick={() => onLesson(null, unit.id)}>Add lesson</Btn>
      </header>
      {lessons.data?.length === 0 && <Empty>No lessons.</Empty>}
      {lessons.data?.map((l) => (
        <button key={l.id} type="button" onClick={() => onLesson(l, unit.id)} className="flex w-full items-center gap-3 border-b border-line px-3 py-1.5 text-left last:border-0 hover:bg-blue-soft/50">
          <span className="flex-1">{nm(l.names)}</span>
          {l.legendary && <Badge tone="gold">legendary</Badge>}
          {l.theory.length > 0 && <Badge>{l.theory.length} theory</Badge>}
          <span className="text-xs text-ink-soft">{l.question_count} q · {l.topic_ids.length} topics · {l.type_ids.length} types</span>
          <PoolBadge g={gateBy.get(l.id)} />
        </button>
      ))}
    </section>
  );
}

function LessonDrawer({ edit, close, setEdit, subjectId, gateBy, invalidate }: { edit: { id?: string; form: LessonIn } | null; close: () => void; setEdit: (e: { id?: string; form: LessonIn } | null) => void; subjectId?: string; gateBy: Gate; invalidate: readonly (readonly unknown[])[] }) {
  const topics = useTopics(subjectId);
  const types = useTypes();
  const unitId = edit?.form.unit_id ?? "";
  const inv = [...invalidate, qk.lessons(unitId)];
  const save = useAct((e: { id?: string; form: LessonIn }) => {
    const body = { ...e.form, names: cleanNames(e.form.names) };
    return e.id ? catalog.lessons.update(e.id, body) : catalog.lessons.create(body);
  }, inv, "Saved");
  const del = useAct((id: string) => catalog.lessons.remove(id), inv, "Deleted");
  const f = edit?.form;
  const set = (p: Partial<LessonIn>) => edit && setEdit({ ...edit, form: { ...edit.form, ...p } });
  return (
    <Drawer open={!!edit} onClose={close} width="max-w-3xl" title={edit?.id ? "Edit lesson" : "New lesson"}
      footer={<>
        {edit?.id && <Btn variant="danger" className="mr-auto" onClick={() => confirm("Delete lesson?") && del.mutate(edit.id!, { onSuccess: close })}>Delete</Btn>}
        <Btn onClick={close}>Cancel</Btn>
        <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(edit!, { onSuccess: close })}>Save</Btn>
      </>}>
      {f && edit && (
        <div className="space-y-3">
          <NamesEditor value={f.names} onChange={(names) => set({ names })} />
          <Field label="Topics" hint="Empty = all topics of the subject"><MultiPick options={(topics.data ?? []).map((t) => ({ id: t.id, label: nm(t.names) }))} value={f.topic_ids ?? []} onChange={(topic_ids) => set({ topic_ids })} /></Field>
          <Field label="Question types" hint="Empty = all types"><MultiPick options={(types.data ?? []).map((t) => ({ id: t.id, label: `${nm(t.names)} · ${t.kind}` }))} value={f.type_ids ?? []} onChange={(type_ids) => set({ type_ids })} /></Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Questions per run (1–100)"><Input type="number" min={1} max={100} value={f.question_count ?? 10} onChange={(e) => set({ question_count: Number(e.target.value) })} /></Field>
            <div className="flex items-end gap-3"><Check checked={f.legendary ?? false} onChange={(legendary) => set({ legendary })} label="Legendary" />{edit.id && <PoolBadge g={gateBy.get(edit.id)} />}</div>
          </div>
          <p className="text-xs text-ink-soft">The pool badge is the saved lesson’s verified-question count vs the minimum needed (launch gate); it refreshes after save.</p>
          <TheoryEditor value={f.theory ?? []} onChange={(theory) => set({ theory })} />
        </div>
      )}
    </Drawer>
  );
}
