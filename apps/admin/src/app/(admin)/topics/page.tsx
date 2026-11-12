"use client";
import { useT } from "@/lib/i18n";
import { useMemo, useState } from "react";
import { catalog, qk, useAct, useSubjects, useTopics, type Topic, type TopicIn } from "@/lib/catalog";
import { fieldErrors, nm } from "@/lib/util";
import { Badge, Btn, Check, Empty, Field, Input, PageHeader, Select, Toolbar } from "@/components/ui/controls";
import { Icon } from "@dtmai/ui";
import { Drawer } from "@/components/ui/overlay";
import { useConfirm } from "@/components/ui/confirm";
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
  const t = useT();
  const [ask, confirmNode] = useConfirm();
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
  }, keys, t("admin.common.saved"));
  const del = useAct((id: string) => catalog.topics.remove(id), keys, t("admin.common.deleted"));
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
  const sib = (tp: Topic, dir: -1 | 1) => {
    const sibs = nodes.filter((n) => (n.t.parent_id ?? null) === (tp.parent_id ?? null)).map((n) => n.t);
    return sibs[sibs.findIndex((x) => x.id === tp.id) + dir];
  };
  const shift = useAct(async (a: { id: string; dir: -1 | 1 }) => {
    const moved = (topics.data ?? []).find((x) => x.id === a.id)!;
    const other = sib(moved, a.dir);
    if (!other) return;
    const order = nodes.map((n) => n.t.id).filter((i) => i !== moved.id);
    const at = order.indexOf(other.id);
    order.splice(a.dir === -1 ? at : at + 1, 0, moved.id);
    await catalog.topics.reorder(sid!, order);
  }, keys);

  const f = edit?.form;
  const fe = fieldErrors(save.error);
  const set = (p: Partial<TopicIn>) => setEdit((e) => e && { ...e, form: { ...e.form, ...p } });
  const open = (t: Topic) => setEdit({ id: t.id, form: { subject_id: t.subject_id, parent_id: t.parent_id ?? null, code: t.code, names: t.names, position: t.position, active: t.active } });
  const descendants = (id: string) => new Set(nodes.slice(nodes.findIndex((n) => n.t.id === id)).filter((n, i, a) => i === 0 || n.depth > a[0]!.depth).map((n) => n.t.id));

  return (
    <>
      <PageHeader title={t("admin.common.topics")} sub={t("admin.topics.dragARowOnto")} actions={<Btn variant="primary" disabled={!sid} onClick={() => setEdit({ form: { subject_id: sid!, parent_id: null, code: "", names: {}, position: nodes.length, active: true } })}>{t("admin.topics.newTopic")}</Btn>} />
      <Toolbar>
        <Field label={t("admin.common.subject")}><Select value={sid ?? ""} onChange={(e) => setSubjectId(e.target.value)}>{subjects.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select></Field>
      </Toolbar>
      <div className="min-h-0 flex-1 overflow-auto bg-white">
        {nodes.length === 0 && <Empty>{topics.isLoading ? t("admin.common.loading") : t("admin.topics.noTopicsForThis")}</Empty>}
        {nodes.map(({ t: tp, depth }) => (
          <div key={tp.id} draggable onDragStart={() => setDrag(tp.id)} onDragEnd={() => { setDrag(null); setOver(null); }}
            onDragOver={(e) => { e.preventDefault(); setOver(tp.id); }}
            onDrop={() => { if (drag && drag !== tp.id && !descendants(drag).has(tp.id)) move.mutate({ id: drag, before: tp.id }); setDrag(null); setOver(null); }}
            onClick={() => open(tp)}
            className={`flex cursor-grab items-center gap-2 border-b border-line px-3 py-1.5 hover:bg-blue-soft/50 ${over === tp.id && drag !== tp.id ? "border-t-2 border-t-blue" : ""} ${drag === tp.id ? "opacity-40" : ""}`}
            style={{ paddingLeft: 12 + depth * 24 }}>
            <Icon name="menu" size={16} className="text-ink-soft" />
            <span className="font-extrabold">{nm(tp.names)}</span>
            <code className="text-xs text-ink-soft">{tp.code}</code>
            {!tp.active && <Badge>{t("admin.topics.inactive")}</Badge>}
            <span className="ml-auto flex gap-1" onClick={(e) => e.stopPropagation()}>
              <button type="button" className="rounded-xl p-1 text-ink-soft hover:bg-snow disabled:opacity-30" aria-label={t("admin.topics.moveUp")} disabled={!sib(tp, -1) || move.isPending} onClick={() => shift.mutate({ id: tp.id, dir: -1 })}><Icon name="arrow-up" size={16} /></button>
              <button type="button" className="rounded-xl p-1 text-ink-soft hover:bg-snow disabled:opacity-30" aria-label={t("admin.topics.moveDown")} disabled={!sib(tp, 1) || move.isPending} onClick={() => shift.mutate({ id: tp.id, dir: 1 })}><Icon name="arrow-down" size={16} /></button>
            </span>
          </div>
        ))}
      </div>
      <Drawer open={!!edit} onClose={() => setEdit(null)} width="max-w-lg" title={edit?.id ? t("admin.topics.editTopic") : t("admin.topics.newTopic")}
        footer={<>
          {edit?.id && <Btn variant="danger" className="mr-auto" onClick={() => ask({ title: t("admin.topics.deleteThisTopic"), name: nm(edit.form.names) || (edit.form.code ?? ""), danger: true, confirmLabel: t("admin.common.delete") }, () => del.mutate(edit.id!, { onSuccess: () => setEdit(null) }))}>{t("admin.common.delete")}</Btn>}
          <Btn onClick={() => setEdit(null)}>{t("admin.common.cancel")}</Btn>
          <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(edit!, { onSuccess: () => setEdit(null) })}>{t("admin.common.save")}</Btn>
        </>}>
        {f && (
          <div className="space-y-3">
            <Field label={t("admin.common.code")} error={fe.code}><Input value={f.code ?? ""} onChange={(e) => set({ code: e.target.value })} /></Field>
            <NamesEditor value={f.names} onChange={(names) => set({ names })} error={fe.names} />
            <Field label={t("admin.topics.parent")} error={fe.parent_id}>
              <Select value={f.parent_id ?? ""} onChange={(e) => set({ parent_id: e.target.value || null })}>
                <option value="">{t("admin.topics.root")}</option>
                {nodes.filter((n) => n.t.id !== edit?.id && !(edit?.id && descendants(edit.id).has(n.t.id))).map((n) => <option key={n.t.id} value={n.t.id}>{"\u00a0".repeat(n.depth * 3)}{nm(n.t.names)}</option>)}
              </Select>
            </Field>
            <Check checked={f.active ?? true} onChange={(active) => set({ active })} label={t("admin.common.active")} />
          </div>
        )}
      </Drawer>
      {confirmNode}
    </>
  );
}
