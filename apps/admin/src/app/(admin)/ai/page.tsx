"use client";
import { useEnum, useT } from "@/lib/i18n";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { AI_TASKS, ai, type Limits, type Route, type Spend } from "@/lib/ai";
import { useAct } from "@/lib/catalog";
import { fieldErrors } from "@/lib/util";
import { Badge, Btn, Check, ErrorBox, Field, Input, PageHeader, Select, Tabs } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";
import { Drawer } from "@/components/ui/overlay";
import { useConfirm } from "@/components/ui/confirm";

const blank: Route = { task: "solve", slot: 0, model: "", temperature: 0.2, max_tokens: 2048, price_in_usd_per_mtok: 0, price_out_usd_per_mtok: 0, enabled: true };
type Rows = Spend["by_day"];
const usd = (n: number) => `$${n.toFixed(n < 1 ? 4 : 2)}`;

function SpendTable({ rows, head }: { rows: Rows; head: string }) {
  const t = useT();
  return <DataTable rows={rows} rowKey={(r) => r.key} empty={t("admin.ai.noSpendRecorded")}
    cols={[{ key: "k", head, cell: (r) => r.key }, { key: "c", head: t("admin.ai.calls"), cell: (r) => r.calls }, { key: "i", head: t("admin.ai.tokensIn"), cell: (r) => r.tokens_in.toLocaleString() }, { key: "o", head: t("admin.ai.tokensOut"), cell: (r) => r.tokens_out.toLocaleString() }, { key: "$", head: t("admin.ai.cost"), cell: (r) => usd(r.cost_usd) }]} />;
}

export default function AiPage() {
  const t = useT();
  const [tab, setTab] = useState<"routes" | "spend">("routes");
  const [days, setDays] = useState(30);
  const routes = useQuery({ queryKey: ["ai-routes"], queryFn: ai.routes });
  const limits = useQuery({ queryKey: ["ai-limits"], queryFn: ai.limits });
  const spend = useQuery({ queryKey: ["ai-spend", days], queryFn: () => ai.spend(days), enabled: tab === "spend" });
  const [edit, setEdit] = useState<Route | null>(null);
  const [creating, setCreating] = useState(false);
  const [ask, confirmNode] = useConfirm();
  const en = useEnum();
  const [lim, setLim] = useState<Limits | null>(null);
  useEffect(() => { if (limits.data) setLim(limits.data); }, [limits.data]);
  const save = useAct((r: Route) => ai.saveRoute(r), [["ai-routes"]], t("admin.ai.routeSaved"));
  const del = useAct((r: Route) => ai.removeRoute(r.task, r.slot ?? 0), [["ai-routes"]], t("admin.ai.routeRemoved"));
  const saveLim = useAct((l: Limits) => ai.saveLimits(l), [["ai-limits"], ["ai-spend"]], t("admin.ai.limitsSaved"));
  const fe = fieldErrors(save.error);
  const le = fieldErrors(saveLim.error);
  const set = (p: Partial<Route>) => setEdit((e) => e && { ...e, ...p });
  const num = (k: keyof Route) => (e: React.ChangeEvent<HTMLInputElement>) => set({ [k]: Number(e.target.value) } as Partial<Route>);
  const collision = !!edit && creating && !!routes.data?.some((r) => r.task === edit.task && (r.slot ?? 0) === (edit.slot ?? 0));
  const valid = !!edit && edit.model.trim() !== "" && (edit.slot ?? 0) >= 0 && (edit.max_tokens ?? 1) >= 1 && (edit.max_tokens ?? 0) <= 32000 && (edit.temperature ?? 0) >= 0;
  return (
    <>
      <PageHeader title={t("admin.ai.aiModelsSpend")} sub={t("admin.ai.modelRoutingPerTask")} actions={tab === "routes" ? <Btn variant="primary" onClick={() => { setCreating(true); setEdit(blank); }}>{t("admin.ai.newRoute")}</Btn> : undefined} />
      <div className="border-b border-line bg-white px-4"><Tabs value={tab} onChange={setTab} items={[{ id: "routes", label: t("admin.ai.routesLimits") }, { id: "spend", label: t("admin.ai.spend") }]} /></div>
      <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">
        {tab === "routes" ? (
          <>
            {lim && (
              <div className="flex flex-wrap items-end gap-3 rounded-xl border border-line bg-white p-4">
                <Check checked={lim.enabled} onChange={(enabled) => setLim({ ...lim, enabled })} label={t("admin.ai.aiEnabled")} />
                <Field label={t("admin.ai.dailySpendCapUsd")} error={le.daily_spend_cap_usd}><Input type="number" step="0.5" min={0} value={lim.daily_spend_cap_usd} onChange={(e) => setLim({ ...lim, daily_spend_cap_usd: Number(e.target.value) })} /></Field>
                <Field label={t("admin.ai.perUserDailyToken")} error={le.user_daily_token_budget}><Input type="number" min={0} step={1} value={lim.user_daily_token_budget} onChange={(e) => setLim({ ...lim, user_daily_token_budget: Number(e.target.value) })} /></Field>
                <Btn variant="primary" disabled={saveLim.isPending} onClick={() => saveLim.mutate(lim)}>{t("admin.ai.saveLimits")}</Btn>
              </div>
            )}
            <DataTable rows={routes.data} loading={routes.isLoading} error={routes.error} rowKey={(r) => `${r.task}:${r.slot ?? 0}`} onRow={(r) => { setCreating(false); setEdit(r); }}
              cols={[
                { key: "t", head: t("admin.ai.task"), cell: (r) => <Badge tone="blue">{en("aiTask", r.task)}</Badge> },
                { key: "s", head: t("admin.ai.slot"), cell: (r) => r.slot ?? 0 },
                { key: "m", head: t("admin.ai.model"), cell: (r) => <code>{r.model}</code> },
                { key: "tp", head: t("admin.ai.temp"), cell: (r) => r.temperature },
                { key: "mt", head: t("admin.ai.maxTokens"), cell: (r) => r.max_tokens },
                { key: "p", head: t("admin.ai.mtokInOut"), cell: (r) => `${r.price_in_usd_per_mtok ?? 0} / ${r.price_out_usd_per_mtok ?? 0}` },
                { key: "e", head: t("admin.common.state"), cell: (r) => <Badge tone={r.enabled ? "green" : "gray"}>{r.enabled ? t("admin.ai.on") : t("admin.ai.off")}</Badge> },
              ]} />
          </>
        ) : (
          <>
            <div className="flex items-center gap-3"><Field label={t("admin.ai.window")}><Select value={days} onChange={(e) => setDays(Number(e.target.value))}>{[7, 30, 90].map((d) => <option key={d} value={d}>{t("admin.ai.days", { n: d })}</option>)}</Select></Field>
              {spend.data && <span className="text-sm">{t("admin.ai.today")} <b>{usd(spend.data.spent_today_usd)}</b> {t("admin.ai.ofCap", { cap: usd(spend.data.daily_spend_cap_usd) })}</span>}</div>
            {spend.isLoading && <p className="text-ink-soft">{t("admin.common.loading")}</p>}
            {spend.error && <ErrorBox error={spend.error} />}
            {spend.data && (
              <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                {([["admin.ai.byDay", "admin.ai.day", spend.data.by_day], ["admin.ai.byTask", "admin.ai.task", spend.data.by_task], ["admin.ai.byModel", "admin.ai.model", spend.data.by_model], ["admin.ai.byPurpose", "admin.ai.purpose", spend.data.by_purpose]] as [string, string, Rows][]).map(([h, c, r]) => <div key={h} className="min-w-0 overflow-x-auto"><h3 className="mb-1 text-sm">{t(h)}</h3><SpendTable rows={r} head={t(c)} /></div>)}
              </div>
            )}
          </>
        )}
      </div>
      <Drawer open={!!edit} onClose={() => setEdit(null)} width="max-w-md" title={t("admin.ai.aiRoute")}
        footer={edit && <>
          {!creating && <Btn variant="danger" className="mr-auto" onClick={() => ask({ title: t("admin.ai.removeRoute"), name: `${en("aiTask", edit.task)} #${edit.slot ?? 0} · ${edit.model}`, danger: true, confirmLabel: t("admin.common.remove") }, () => del.mutate(edit, { onSuccess: () => setEdit(null) }))}>{t("admin.common.remove")}</Btn>}
          <Btn onClick={() => setEdit(null)}>{t("admin.common.cancel")}</Btn>
          <Btn variant="primary" disabled={!valid || save.isPending} onClick={() => save.mutate(edit, { onSuccess: () => setEdit(null) })}>{t("admin.common.save")}</Btn></>}>
        {edit && (
          <div className="space-y-3">
            {collision && <p role="alert" className="rounded-xl border-2 border-gold bg-white p-2 text-sm font-bold">{t("admin.ai.slotCollision")}</p>}
            <div className="grid grid-cols-2 gap-3">
              <Field label={t("admin.ai.task")} error={fe.task}><Select value={edit.task} disabled={!creating} onChange={(e) => set({ task: e.target.value as Route["task"] })}>{AI_TASKS.map((k) => <option key={k} value={k}>{en("aiTask", k)}</option>)}</Select></Field>
              <Field label={t("admin.ai.slot")} error={fe.slot}><Input type="number" min={0} step={1} disabled={!creating} value={edit.slot ?? 0} onChange={num("slot")} /></Field>
            </div>
            <Field label={t("admin.ai.modelOpenrouterId")} error={!edit.model.trim() ? t("admin.common.required") : fe.model}><Input value={edit.model} onChange={(e) => set({ model: e.target.value })} placeholder={t("admin.ai.googleGemini25")} /></Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label={t("admin.ai.temperature")} error={fe.temperature}><Input type="number" step="0.1" min={0} max={2} value={edit.temperature ?? 0.2} onChange={num("temperature")} /></Field>
              <Field label={t("admin.ai.maxTokens")} error={fe.max_tokens}><Input type="number" min={1} max={32000} step={1} value={edit.max_tokens ?? 0} onChange={num("max_tokens")} /></Field>
              <Field label={t("admin.ai.priceInMtok")} error={fe.price_in_usd_per_mtok}><Input type="number" step="0.01" min={0} value={edit.price_in_usd_per_mtok ?? 0} onChange={num("price_in_usd_per_mtok")} /></Field>
              <Field label={t("admin.ai.priceOutMtok")} error={fe.price_out_usd_per_mtok}><Input type="number" step="0.01" min={0} value={edit.price_out_usd_per_mtok ?? 0} onChange={num("price_out_usd_per_mtok")} /></Field>
            </div>
            <Check checked={edit.enabled ?? true} onChange={(enabled) => set({ enabled })} label={t("admin.ai.enabled")} />
          </div>
        )}
      </Drawer>
      {confirmNode}
    </>
  );
}
