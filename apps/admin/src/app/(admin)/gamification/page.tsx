"use client";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { gamification, type GameConfig, type QuestTemplateIn, type Tier } from "@/lib/gamification";
import { useAct } from "@/lib/catalog";
import { nm } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader, Tabs } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";
import { Drawer } from "@/components/ui/overlay";
import { NamesEditor, cleanNames } from "@/components/ui/names";

const blank: QuestTemplateIn = { code: "", metric: "xp", target: 50, reward_gems: 5, reward_xp: 0, title: {}, active: true };

function Quests() {
  const q = useQuery({ queryKey: ["quest-templates"], queryFn: gamification.quests });
  const [edit, setEdit] = useState<{ id?: string; form: QuestTemplateIn } | null>(null);
  const save = useAct((e: { id?: string; form: QuestTemplateIn }) => {
    const body = { ...e.form, title: cleanNames(e.form.title ?? {}) };
    return e.id ? gamification.updateQuest(e.id, body) : gamification.createQuest(body);
  }, [["quest-templates"]], "Saved");
  const f = edit?.form;
  const set = (p: Partial<QuestTemplateIn>) => setEdit((e) => e && { ...e, form: { ...e.form, ...p } });
  const n = (k: keyof QuestTemplateIn) => (e: React.ChangeEvent<HTMLInputElement>) => set({ [k]: Number(e.target.value) } as Partial<QuestTemplateIn>);
  return (
    <>
      <div className="flex justify-end p-3"><Btn variant="primary" onClick={() => setEdit({ form: blank })}>New quest template</Btn></div>
      <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(r) => r.id} onRow={(r) => setEdit({ id: r.id, form: { code: r.code, metric: r.metric, target: r.target, reward_gems: r.reward_gems, reward_xp: r.reward_xp, title: r.title ?? {}, active: r.active } })}
        cols={[
          { key: "c", head: "Code", cell: (r) => <code>{r.code}</code> },
          { key: "t", head: "Title", cell: (r) => nm(r.title) },
          { key: "m", head: "Metric", cell: (r) => r.metric },
          { key: "g", head: "Target", cell: (r) => r.target },
          { key: "r", head: "Reward", cell: (r) => `${r.reward_gems ?? 0} gems · ${r.reward_xp ?? 0} XP` },
          { key: "a", head: "State", cell: (r) => <Badge tone={r.active ? "green" : "gray"}>{r.active ? "active" : "off"}</Badge> },
        ]} />
      <Drawer open={!!edit} onClose={() => setEdit(null)} width="max-w-md" title={edit?.id ? "Edit quest" : "New quest"}
        footer={<><Btn onClick={() => setEdit(null)}>Cancel</Btn><Btn variant="primary" disabled={save.isPending || !f?.code} onClick={() => save.mutate(edit!, { onSuccess: () => setEdit(null) })}>Save</Btn></>}>
        {f && <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3"><Field label="Code"><Input value={f.code} onChange={(e) => set({ code: e.target.value })} /></Field><Field label="Metric" hint="e.g. xp, lessons, correct_answers"><Input value={f.metric} onChange={(e) => set({ metric: e.target.value })} /></Field></div>
          <NamesEditor value={f.title ?? {}} onChange={(title) => set({ title })} />
          <div className="grid grid-cols-3 gap-3"><Field label="Target"><Input type="number" value={f.target} onChange={n("target")} /></Field><Field label="Gems"><Input type="number" value={f.reward_gems ?? 0} onChange={n("reward_gems")} /></Field><Field label="XP"><Input type="number" value={f.reward_xp ?? 0} onChange={n("reward_xp")} /></Field></div>
          <Check checked={f.active ?? true} onChange={(active) => set({ active })} label="Active" />
        </div>}
      </Drawer>
    </>
  );
}

function Leagues() {
  const t = useQuery({ queryKey: ["league-tiers"], queryFn: gamification.tiers });
  const [tiers, setTiers] = useState<Tier[]>([]);
  useEffect(() => { if (t.data) setTiers(t.data); }, [t.data]);
  const save = useAct((x: Tier[]) => gamification.saveTiers(x), [["league-tiers"]], "Tiers saved");
  const roll = useAct(() => gamification.rollover(), [], "Rollover done");
  const upd = (i: number, p: Partial<Tier>) => setTiers((ts) => ts.map((x, j) => (j === i ? { ...x, ...p } : x)));
  return (
    <div className="space-y-3 p-4">
      <DataTable rows={tiers} loading={t.isLoading} error={t.error} rowKey={(r) => r.code}
        cols={[
          { key: "i", head: "#", cell: (r) => r.idx },
          { key: "c", head: "Code", cell: (r) => <code>{r.code}</code> },
          { key: "n", head: "Name", cell: (r) => nm(r.name) },
          ...(["cohort_size", "promote_count", "demote_count"] as const).map((k) => ({ key: k, head: k.replace("_", " "), cell: (r: Tier) => <Input className="w-20" type="number" value={r[k]} onChange={(e) => upd(tiers.indexOf(r), { [k]: Number(e.target.value) })} /> })),
        ]} />
      <div className="flex gap-2">
        <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(tiers)}>Save tiers</Btn>
        <Btn variant="danger" disabled={roll.isPending} onClick={() => confirm("Settle the current week and promote/demote everyone now?") && roll.mutate(undefined, { onSuccess: (r) => alert(`${r.settled_cohorts} cohorts settled`) })}>Run weekly rollover now</Btn>
      </div>
    </div>
  );
}

const LABELS: Record<keyof GameConfig, string> = {
  heart_refill_minutes: "Heart refill (minutes)", xp_daily_cap: "XP daily cap", xp_session_cap: "XP per session cap", xp_per_item_cap: "XP per item cap", mock_xp: "XP per mock",
  freeze_cost_gems: "Streak freeze cost (gems)", freeze_max: "Max streak freezes", review_correct_per_heart: "Correct review answers per heart", daily_quest_count: "Daily quests per user",
};
function Rules() {
  const c = useQuery({ queryKey: ["game-config"], queryFn: gamification.config });
  const [f, setF] = useState<GameConfig | null>(null);
  useEffect(() => { if (c.data) setF(c.data); }, [c.data]);
  const save = useAct((x: GameConfig) => gamification.saveConfig(x), [["game-config"]], "Rules saved");
  if (!f) return <div className="p-4 text-ink-soft">Loading…</div>;
  return (
    <div className="max-w-2xl space-y-3 p-4">
      <div className="grid grid-cols-2 gap-3">{(Object.keys(LABELS) as (keyof GameConfig)[]).map((k) => <Field key={k} label={LABELS[k]}><Input type="number" value={f[k]} onChange={(e) => setF({ ...f, [k]: Number(e.target.value) })} /></Field>)}</div>
      <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(f)}>Save rules</Btn>
    </div>
  );
}

export default function GamificationPage() {
  const [tab, setTab] = useState<"quests" | "leagues" | "rules">("quests");
  return (
    <>
      <PageHeader title="Quests & leagues" sub="Daily quest templates, league tiers and economy rules." />
      <div className="border-b border-line bg-white px-4"><Tabs value={tab} onChange={setTab} items={[{ id: "quests", label: "Quest templates" }, { id: "leagues", label: "League tiers" }, { id: "rules", label: "Economy rules" }]} /></div>
      <div className="min-h-0 flex-1 overflow-auto">{tab === "quests" ? <Quests /> : tab === "leagues" ? <Leagues /> : <Rules />}</div>
    </>
  );
}
