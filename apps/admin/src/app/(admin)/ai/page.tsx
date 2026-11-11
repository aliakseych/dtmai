"use client";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { AI_TASKS, ai, type Limits, type Route, type Spend } from "@/lib/ai";
import { useAct } from "@/lib/catalog";
import { Badge, Btn, Check, Field, Input, PageHeader, Select, Tabs } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";
import { Drawer } from "@/components/ui/overlay";

const blank: Route = { task: "solve", slot: 0, model: "", temperature: 0, max_tokens: 2048, price_in_usd_per_mtok: 0, price_out_usd_per_mtok: 0, enabled: true };
type Rows = Spend["by_day"];
const usd = (n: number) => `$${n.toFixed(n < 1 ? 4 : 2)}`;

function SpendTable({ rows, head }: { rows: Rows; head: string }) {
  return <DataTable rows={rows} rowKey={(r) => r.key} empty="No spend recorded."
    cols={[{ key: "k", head, cell: (r) => r.key }, { key: "c", head: "Calls", cell: (r) => r.calls }, { key: "i", head: "Tokens in", cell: (r) => r.tokens_in.toLocaleString() }, { key: "o", head: "Tokens out", cell: (r) => r.tokens_out.toLocaleString() }, { key: "$", head: "Cost", cell: (r) => usd(r.cost_usd) }]} />;
}

export default function AiPage() {
  const [tab, setTab] = useState<"routes" | "spend">("routes");
  const [days, setDays] = useState(30);
  const routes = useQuery({ queryKey: ["ai-routes"], queryFn: ai.routes });
  const limits = useQuery({ queryKey: ["ai-limits"], queryFn: ai.limits });
  const spend = useQuery({ queryKey: ["ai-spend", days], queryFn: () => ai.spend(days), enabled: tab === "spend" });
  const [edit, setEdit] = useState<Route | null>(null);
  const [lim, setLim] = useState<Limits | null>(null);
  useEffect(() => { if (limits.data) setLim(limits.data); }, [limits.data]);
  const save = useAct((r: Route) => ai.saveRoute(r), [["ai-routes"]], "Route saved");
  const del = useAct((r: Route) => ai.removeRoute(r.task, r.slot ?? 0), [["ai-routes"]], "Route removed");
  const saveLim = useAct((l: Limits) => ai.saveLimits(l), [["ai-limits"], ["ai-spend"]], "Limits saved");
  const set = (p: Partial<Route>) => setEdit((e) => e && { ...e, ...p });
  const num = (k: keyof Route) => (e: React.ChangeEvent<HTMLInputElement>) => set({ [k]: Number(e.target.value) } as Partial<Route>);
  return (
    <>
      <PageHeader title="AI models & spend" sub="Model routing per task (slot 0 is primary; extra slots are voters/fallbacks), budgets and spend." actions={tab === "routes" ? <Btn variant="primary" onClick={() => setEdit(blank)}>New route</Btn> : undefined} />
      <div className="border-b border-line bg-white px-4"><Tabs value={tab} onChange={setTab} items={[{ id: "routes", label: "Routes & limits" }, { id: "spend", label: "Spend" }]} /></div>
      <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">
        {tab === "routes" ? (
          <>
            {lim && (
              <div className="flex items-end gap-3 rounded-xl border border-line bg-white p-4">
                <Check checked={lim.enabled} onChange={(enabled) => setLim({ ...lim, enabled })} label="AI enabled" />
                <Field label="Daily spend cap (USD)"><Input type="number" step="0.5" value={lim.daily_spend_cap_usd} onChange={(e) => setLim({ ...lim, daily_spend_cap_usd: Number(e.target.value) })} /></Field>
                <Field label="Per-user daily token budget"><Input type="number" value={lim.user_daily_token_budget} onChange={(e) => setLim({ ...lim, user_daily_token_budget: Number(e.target.value) })} /></Field>
                <Btn variant="primary" disabled={saveLim.isPending} onClick={() => saveLim.mutate(lim)}>Save limits</Btn>
              </div>
            )}
            <DataTable rows={routes.data} loading={routes.isLoading} error={routes.error} rowKey={(r) => `${r.task}:${r.slot ?? 0}`} onRow={setEdit}
              cols={[
                { key: "t", head: "Task", cell: (r) => <Badge tone="blue">{r.task}</Badge> },
                { key: "s", head: "Slot", cell: (r) => r.slot ?? 0 },
                { key: "m", head: "Model", cell: (r) => <code>{r.model}</code> },
                { key: "tp", head: "Temp", cell: (r) => r.temperature },
                { key: "mt", head: "Max tokens", cell: (r) => r.max_tokens },
                { key: "p", head: "$/Mtok in / out", cell: (r) => `${r.price_in_usd_per_mtok ?? 0} / ${r.price_out_usd_per_mtok ?? 0}` },
                { key: "e", head: "State", cell: (r) => <Badge tone={r.enabled ? "green" : "gray"}>{r.enabled ? "on" : "off"}</Badge> },
              ]} />
          </>
        ) : (
          <>
            <div className="flex items-center gap-3"><Field label="Window"><Select value={days} onChange={(e) => setDays(Number(e.target.value))}>{[7, 30, 90].map((d) => <option key={d} value={d}>{d} days</option>)}</Select></Field>
              {spend.data && <span className="text-sm">Today <b>{usd(spend.data.spent_today_usd)}</b> of cap {usd(spend.data.daily_spend_cap_usd)}</span>}</div>
            {spend.data && (
              <div className="grid grid-cols-2 gap-4">
                {([["By day", spend.data.by_day], ["By task", spend.data.by_task], ["By model", spend.data.by_model], ["By purpose", spend.data.by_purpose]] as [string, Rows][]).map(([h, r]) => <div key={h}><h3 className="mb-1 text-sm">{h}</h3><SpendTable rows={r} head={h.replace("By ", "")} /></div>)}
              </div>
            )}
          </>
        )}
      </div>
      <Drawer open={!!edit} onClose={() => setEdit(null)} width="max-w-md" title="AI route"
        footer={edit && <>
          <Btn variant="danger" className="mr-auto" onClick={() => confirm("Remove route?") && del.mutate(edit, { onSuccess: () => setEdit(null) })}>Remove</Btn>
          <Btn onClick={() => setEdit(null)}>Cancel</Btn>
          <Btn variant="primary" disabled={!edit.model || save.isPending} onClick={() => save.mutate(edit, { onSuccess: () => setEdit(null) })}>Save</Btn></>}>
        {edit && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <Field label="Task"><Select value={edit.task} onChange={(e) => set({ task: e.target.value as Route["task"] })}>{AI_TASKS.map((t) => <option key={t}>{t}</option>)}</Select></Field>
              <Field label="Slot"><Input type="number" min={0} value={edit.slot ?? 0} onChange={num("slot")} /></Field>
            </div>
            <Field label="Model (OpenRouter id)"><Input value={edit.model} onChange={(e) => set({ model: e.target.value })} placeholder="google/gemini-2.5-pro" /></Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Temperature"><Input type="number" step="0.1" value={edit.temperature ?? 0} onChange={num("temperature")} /></Field>
              <Field label="Max tokens"><Input type="number" value={edit.max_tokens ?? 0} onChange={num("max_tokens")} /></Field>
              <Field label="Price in ($/Mtok)"><Input type="number" step="0.01" value={edit.price_in_usd_per_mtok ?? 0} onChange={num("price_in_usd_per_mtok")} /></Field>
              <Field label="Price out ($/Mtok)"><Input type="number" step="0.01" value={edit.price_out_usd_per_mtok ?? 0} onChange={num("price_out_usd_per_mtok")} /></Field>
            </div>
            <Check checked={edit.enabled ?? true} onChange={(enabled) => set({ enabled })} label="Enabled" />
          </div>
        )}
      </Drawer>
    </>
  );
}
