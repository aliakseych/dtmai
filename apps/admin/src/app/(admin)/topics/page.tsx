"use client";
import { useMemo, useState } from "react";
import { catalog, qk, useAct, useSubjects, useTopics, type Topic, type TopicIn } from "@/lib/catalog";
import { nm } from "@/lib/util";
import { Badge, Btn, Check, Empty, Field, Input, PageHeader, Select, Toolbar } from "@/components/ui/controls";
import { Drawer } from "@/components/ui/overlay";
import { NamesEditor, cleanNames } from "@/components/ui/names";

interface Node { t: Topic; depth: number }

/** Depth-first flatten honouring `position` among siblings. */
function flatten(all: Topic[]): Node[] {
  const kids = new Map<string | null, Topic[]>();
  for (const t of all) kids.set(t.parent_id ?? null, [...(kids.get(t.parent_id ?? null) ?? []), t]);
  const out: Node[] = [];
  const walk = (p: string | null, depth: number) => {
    for (const t of (kids.get(p) ?? []).sort((a, b) => a.position - b.position)) {
      out.push({ t, depth });
      walk(t.id, depth + 1);
    }
  };
  walk(null, 0);
  return out;
}

export default function TopicsPage() {
  const subjects = useSubjects();
  const [subjectId, setSubjectId] = useState("");
  const sid = subjectId || subjects.data?.[0]?.id;
  const topics = useTopics(sid);
  const nodes = useMemo(() => flatten(topics.data ?? []), [topics.data]);
  const [drag, setDrag] = useState<string | null>(null);
  const [over, setOver] = useState<string | null>(null);
  const [edit, setEdit] = useState<{ id?: string; form: TopicIn } | null>(null);
  const keys = [qk.topics(sid ?? "")];

  const save = useAct((e: { id?: string; form: TopicIn }) => {
    const body = { ...e.form, names: cleanNames(e.form.names) };
    return e.id ? catalog.topics.update(e.id, body) : catalog.topics.create(body);
  }, keys, "Saved");
  const del = useAct((id: string) => catalog.topics.remove(id), keys, "Deleted");
  const move = useAct(async (a: { id: string; before: string }) => {
    const all = topics.data ?? [];
    const moved = all.find((t) => t.id === a.id)!;
    const target = all.find((t) => t.id === a.before)!;
    if ((moved.parent_id ?? null) !== (target.parent_id ?? null)) await catalog.topics.update(moved.id, { parent_id: target.parent_id ?? null });
    // Reorder is a permutation of the whole subject: siblings keep relative order, `moved` goes right before `target`.
    const order = nodes.map((n) => n.t.id).filter((i) => i !== moved.id);
    order.splice(order.indexOf(target.id), 0, moved.id);
    await catalog.topics.reorder(sid!, order);
  }, keys);

  const f = edit?.form;
  const set = (p: Partial<TopicIn>) => setEdit((e) => e && { ...e, form: { ...e.form, ...p } });
  const open = (t: Topic) => setEdit({ id: t.id, form: { subject_id: t.subject_id, parent_id: t.parent_id ?? null, code: t.code, names: t.names, position: t.position, active: t.active } });
  const descendants = (id: string) => new Set(nodes.slice(nodes.findIndex((n) => n.t.id === id)).filter((n, i, a) => i === 0 || n.depth > a[0]!.depth).map((n) => n.t.id));

  return (
    <>
      <PageHeader title="Topics" sub="Drag a row onto another to place it before that row (and under its parent)." actions={<Btn variant="primary" disabled={!sid} onClick={() => setEdit({ form: { subject_id: sid!, parent_id: null, code: "", names: {}, position: nodes.length, active: true } })}>New topic</Btn>} />
      <Toolbar>
        <Field label="Subject"><Select value={sid ?? ""} onChange={(e) => setSubjectId(e.target.value)}>{subjects.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select></Field>
      </Toolbar>
      <div className="min-h-0 flex-1 overflow-auto bg-white">
        {nodes.length === 0 && <Empty>{topics.isLoading ? "Loading…" : "No topics for this subject."}</Empty>}
        {nodes.map(({ t, depth }) => (
          <div key={t.id} draggable onDragStart={() => setDrag(t.id)} onDragEnd={() => { setDrag(null); setOver(null); }}
            onDragOver={(e) => { e.preventDefault(); setOver(t.id); }}
            onDrop={() => { if (drag && drag !== t.id && !descendants(drag).has(t.id)) move.mutate({ id: drag, before: t.id }); setDrag(null); setOver(null); }}
            onClick={() => open(t)}
            className={`flex cursor-grab items-center gap-2 border-b border-line px-3 py-1.5 hover:bg-blue-soft/50 ${over === t.id && drag !== t.id ? "border-t-2 border-t-blue" : ""} ${drag === t.id ? "opacity-40" : ""}`}
            style={{ paddingLeft: 12 + depth * 24 }}>
            <span className="text-ink-soft">⠿</span>
            <span className="font-extrabold">{nm(t.names)}</span>
            <code className="text-xs text-ink-soft">{t.code}</code>
            {!t.active && <Badge>inactive</Badge>}
          </div>
        ))}
      </div>
      <Drawer open={!!edit} onClose={() => setEdit(null)} width="max-w-lg" title={edit?.id ? "Edit topic" : "New topic"}
        footer={<>
          {edit?.id && <Btn variant="danger" className="mr-auto" onClick={() => confirm("Delete this topic?") && del.mutate(edit.id!, { onSuccess: () => setEdit(null) })}>Delete</Btn>}
          <Btn onClick={() => setEdit(null)}>Cancel</Btn>
          <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(edit!, { onSuccess: () => setEdit(null) })}>Save</Btn>
        </>}>
        {f && (
          <div className="space-y-3">
            <Field label="Code"><Input value={f.code ?? ""} onChange={(e) => set({ code: e.target.value })} /></Field>
            <NamesEditor value={f.names} onChange={(names) => set({ names })} />
            <Field label="Parent">
              <Select value={f.parent_id ?? ""} onChange={(e) => set({ parent_id: e.target.value || null })}>
                <option value="">— root —</option>
                {nodes.filter((n) => n.t.id !== edit?.id && !(edit?.id && descendants(edit.id).has(n.t.id))).map((n) => <option key={n.t.id} value={n.t.id}>{"\u00a0".repeat(n.depth * 3)}{nm(n.t.names)}</option>)}
              </Select>
            </Field>
            <Check checked={f.active ?? true} onChange={(active) => set({ active })} label="Active" />
          </div>
        )}
      </Drawer>
    </>
  );
}
