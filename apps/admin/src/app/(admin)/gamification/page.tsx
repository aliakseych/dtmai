"use client";
import { useEnum, useT } from "@/lib/i18n";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { gamification, type GameConfig, type QuestTemplateIn, type Tier } from "@/lib/gamification";
import { useAct } from "@/lib/catalog";
import { nm } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader, Tabs } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";
import { Drawer } from "@/components/ui/overlay";
import { useConfirm } from "@/components/ui/confirm";
import { NamesEditor, cleanNames } from "@/components/ui/names";

const blank: QuestTemplateIn = { code: "", metric: "xp", target: 50, reward_gems: 5, reward_xp: 0, title: {}, active: true };

function Quests() {
  const t = useT();
  const en = useEnum();
  const q = useQuery({ queryKey: ["quest-templates"], queryFn: gamification.quests });
  const [edit, setEdit] = useState<{ id?: string; form: QuestTemplateIn } | null>(null);
  const save = useAct((e: { id?: string; form: QuestTemplateIn }) => {
    const body = { ...e.form, title: cleanNames(e.form.title ?? {}) };
    return e.id ? gamification.updateQuest(e.id, body) : gamification.createQuest(body);
  }, [["quest-templates"]], t("admin.common.saved"));
  const f = edit?.form;
  const set = (p: Partial<QuestTemplateIn>) => setEdit((e) => e && { ...e, form: { ...e.form, ...p } });
  const n = (k: keyof QuestTemplateIn) => (e: React.ChangeEvent<HTMLInputElement>) => set({ [k]: Number(e.target.value) } as Partial<QuestTemplateIn>);
  return (
    <>
      <div className="flex justify-end p-3"><Btn variant="primary" onClick={() => setEdit({ form: blank })}>{t("admin.gamification.newQuestTemplate")}</Btn></div>
      <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(r) => r.id} onRow={(r) => setEdit({ id: r.id, form: { code: r.code, metric: r.metric, target: r.target, reward_gems: r.reward_gems, reward_xp: r.reward_xp, title: r.title ?? {}, active: r.active } })}
        cols={[
          { key: "c", head: t("admin.common.code"), cell: (r) => <code>{r.code}</code> },
          { key: "t", head: t("admin.common.title"), cell: (r) => nm(r.title) },
          { key: "m", head: t("admin.gamification.metric"), cell: (r) => en("metric", r.metric) },
          { key: "g", head: t("admin.gamification.target"), cell: (r) => r.target },
          { key: "r", head: t("admin.gamification.reward"), cell: (r) => `${r.reward_gems ?? 0} ${t("admin.gamification.gems")} · ${r.reward_xp ?? 0} ${t("admin.common.xp")}` },
          { key: "a", head: t("admin.common.state"), cell: (r) => <Badge tone={r.active ? "green" : "gray"}>{r.active ? t("admin.common.active") : t("admin.topics.inactive")}</Badge> },
        ]} />
      <Drawer open={!!edit} onClose={() => setEdit(null)} width="max-w-md" title={edit?.id ? t("admin.gamification.editQuest") : t("admin.gamification.newQuest")}
        footer={<><Btn onClick={() => setEdit(null)}>{t("admin.common.cancel")}</Btn><Btn variant="primary" disabled={save.isPending || !f?.code} onClick={() => save.mutate(edit!, { onSuccess: () => setEdit(null) })}>{t("admin.common.save")}</Btn></>}>
        {f && <div className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3"><Field label={t("admin.common.code")}><Input value={f.code} onChange={(e) => set({ code: e.target.value })} /></Field><Field label={t("admin.gamification.metric")} hint={t("admin.gamification.eGXpLessons")}><Input value={f.metric} onChange={(e) => set({ metric: e.target.value })} /></Field></div>
          <NamesEditor value={f.title ?? {}} onChange={(title) => set({ title })} />
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3"><Field label={t("admin.gamification.target")}><Input type="number" value={f.target} onChange={n("target")} /></Field><Field label={t("admin.gamification.gems")}><Input type="number" value={f.reward_gems ?? 0} onChange={n("reward_gems")} /></Field><Field label={t("admin.common.xp")}><Input type="number" value={f.reward_xp ?? 0} onChange={n("reward_xp")} /></Field></div>
          <Check checked={f.active ?? true} onChange={(active) => set({ active })} label={t("admin.common.active")} />
        </div>}
      </Drawer>
    </>
  );
}

function Leagues() {
  const t = useT();
  const tq = useQuery({ queryKey: ["league-tiers"], queryFn: gamification.tiers });
  const [tiers, setTiers] = useState<Tier[]>([]);
  useEffect(() => { if (tq.data) setTiers(tq.data); }, [tq.data]);
  const save = useAct((x: Tier[]) => gamification.saveTiers(x), [["league-tiers"]], t("admin.gamification.tiersSaved"));
  const roll = useAct(() => gamification.rollover(), [], t("admin.gamification.rolloverDone"));
  const [ask, confirmNode] = useConfirm();
  const [settled, setSettled] = useState<number | null>(null);
  const upd = (i: number, p: Partial<Tier>) => setTiers((ts) => ts.map((x, j) => (j === i ? { ...x, ...p } : x)));
  return (
    <div className="space-y-3 p-4">
      <DataTable rows={tiers} loading={tq.isLoading} error={tq.error} rowKey={(r) => r.code}
        cols={[
          { key: "i", head: "#", cell: (r) => r.idx },
          { key: "c", head: t("admin.common.code"), cell: (r) => <code>{r.code}</code> },
          { key: "n", head: t("admin.common.name"), cell: (r) => nm(r.name) },
          ...(["cohort_size", "promote_count", "demote_count"] as const).map((k) => ({ key: k, head: k.replace("_", " "), cell: (r: Tier) => <Input className="w-20" type="number" value={r[k]} onChange={(e) => upd(tiers.indexOf(r), { [k]: Number(e.target.value) })} /> })),
        ]} />
      <div className="flex gap-2">
        <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(tiers)}>{t("admin.gamification.saveTiers")}</Btn>
        <Btn variant="danger" disabled={roll.isPending} onClick={() => ask({ title: t("admin.gamification.settleTheCurrentWeek"), danger: true, confirmLabel: t("admin.gamification.runWeeklyRolloverNow") }, () => roll.mutate(undefined, { onSuccess: (r) => setSettled(r.settled_cohorts) }))}>{t("admin.gamification.runWeeklyRolloverNow")}</Btn>
        {settled !== null && <span role="status" className="self-center text-sm">{t("admin.gamification.settled", { n: settled })}</span>}
      </div>
      {confirmNode}
    </div>
  );
}

const CFG_KEYS: (keyof GameConfig)[] = ["heart_refill_minutes", "xp_daily_cap", "xp_session_cap", "xp_per_item_cap", "mock_xp", "freeze_cost_gems", "freeze_max", "review_correct_per_heart", "daily_quest_count"];
function Rules() {
  const t = useT();
  const c = useQuery({ queryKey: ["game-config"], queryFn: gamification.config });
  const [f, setF] = useState<GameConfig | null>(null);
  useEffect(() => { if (c.data) setF(c.data); }, [c.data]);
  const save = useAct((x: GameConfig) => gamification.saveConfig(x), [["game-config"]], t("admin.gamification.rulesSaved"));
  if (!f) return <div className="p-4 text-ink-soft">{t("admin.common.loading")}</div>;
  return (
    <div className="max-w-2xl space-y-3 p-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">{CFG_KEYS.map((k) => <Field key={k} label={t(`admin.gamification.cfg.${k}`)}><Input type="number" value={f[k]} onChange={(e) => setF({ ...f, [k]: Number(e.target.value) })} /></Field>)}</div>
      <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(f)}>{t("admin.gamification.saveRules")}</Btn>
    </div>
  );
}

export default function GamificationPage() {
  const t = useT();
  const [tab, setTab] = useState<"quests" | "leagues" | "rules">("quests");
  return (
    <>
      <PageHeader title={t("admin.gamification.questsLeagues")} sub={t("admin.gamification.dailyQuestTemplatesLeague")} />
      <div className="border-b border-line bg-white px-4"><Tabs value={tab} onChange={setTab} items={[{ id: "quests", label: t("admin.gamification.questTemplates") }, { id: "leagues", label: t("admin.gamification.leagueTiers") }, { id: "rules", label: t("admin.gamification.economyRules") }]} /></div>
      <div className="min-h-0 flex-1 overflow-auto">{tab === "quests" ? <Quests /> : tab === "leagues" ? <Leagues /> : <Rules />}</div>
    </>
  );
}
