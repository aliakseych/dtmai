"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { billing, type Plan, type PlanCreate } from "@/lib/billing";
import { useAct } from "@/lib/catalog";
import { fmtDate, nm } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader, Select, Tabs } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";
import { Drawer } from "@/components/ui/overlay";
import { NamesEditor, cleanNames } from "@/components/ui/names";
import { JsonEditor } from "@/components/ui/json";

const blank: PlanCreate = { code: "", names: {}, price_uzs: 49000, period_months: 1, features: [], limits: {}, active: true, sort_order: 0 };

export default function BillingPage() {
  const [tab, setTab] = useState<"plans" | "grants">("plans");
  const plans = useQuery({ queryKey: ["billing-plans"], queryFn: billing.plans });
  const [edit, setEdit] = useState<{ isNew: boolean; form: PlanCreate } | null>(null);
  const save = useAct((e: { isNew: boolean; form: PlanCreate }) => {
    const form = { ...e.form, names: cleanNames(e.form.names) };
    if (e.isNew) return billing.createPlan(form);
    const { code, ...patch } = form;
    return billing.updatePlan(code, patch);
  }, [["billing-plans"]], "Plan saved");
  const del = useAct((code: string) => billing.removePlan(code), [["billing-plans"]], "Plan deleted");
  const f = edit?.form;
  const set = (p: Partial<PlanCreate>) => setEdit((e) => e && { ...e, form: { ...e.form, ...p } });

  const [userId, setUserId] = useState("");
  const [lookup, setLookup] = useState("");
  const subs = useQuery({ queryKey: ["billing-subs", lookup], queryFn: () => billing.subscriptions(lookup), enabled: !!lookup });
  const [grant, setGrant] = useState({ plan: "", months: 1 });
  const give = useAct(() => billing.grant({ user_id: lookup, plan_code: grant.plan, months: grant.months }), [["billing-subs"]], "Granted");
  const revoke = useAct((id: string) => billing.revoke(id), [["billing-subs"]], "Revoked");

  return (
    <>
      <PageHeader title="Plans & grants" sub="Premium pricing variants and manual subscription grants." actions={tab === "plans" ? <Btn variant="primary" onClick={() => setEdit({ isNew: true, form: blank })}>New plan</Btn> : undefined} />
      <div className="border-b border-line bg-white px-4"><Tabs value={tab} onChange={setTab} items={[{ id: "plans", label: "Plans" }, { id: "grants", label: "Grants & subscriptions" }]} /></div>
      <div className="min-h-0 flex-1 overflow-auto">
        {tab === "plans" ? (
          <DataTable rows={plans.data} loading={plans.isLoading} error={plans.error} rowKey={(r) => r.code} onRow={(p: Plan) => setEdit({ isNew: false, form: { code: p.code, names: p.names, price_uzs: p.price_uzs, period_months: p.period_months, features: p.features, limits: p.limits, active: p.active, sort_order: p.sort_order } })}
            cols={[
              { key: "c", head: "Code", cell: (r) => <code>{r.code}</code> },
              { key: "n", head: "Name", cell: (r) => nm(r.names) },
              { key: "p", head: "Price (UZS)", cell: (r) => r.price_uzs.toLocaleString() },
              { key: "m", head: "Months", cell: (r) => r.period_months },
              { key: "f", head: "Features", cell: (r) => r.features.join(", ") },
              { key: "a", head: "State", cell: (r) => <Badge tone={r.active ? "green" : "gray"}>{r.active ? "active" : "inactive"}</Badge> },
            ]} />
        ) : (
          <div className="space-y-4 p-4">
            <div className="flex items-end gap-3 rounded-xl border border-line bg-white p-4">
              <Field label="User ID" hint="UUID from the Users screen."><Input className="w-80" value={userId} onChange={(e) => setUserId(e.target.value.trim())} /></Field>
              <Btn variant="primary" disabled={!userId} onClick={() => setLookup(userId)}>Load subscriptions</Btn>
            </div>
            {lookup && (
              <>
                <div className="flex items-end gap-3 rounded-xl border border-line bg-white p-4">
                  <Field label="Grant plan"><Select value={grant.plan} onChange={(e) => setGrant({ ...grant, plan: e.target.value })}><option value="">—</option>{plans.data?.map((p) => <option key={p.code} value={p.code}>{p.code}</option>)}</Select></Field>
                  <Field label="Months"><Input type="number" min={1} max={36} value={grant.months} onChange={(e) => setGrant({ ...grant, months: Number(e.target.value) })} /></Field>
                  <Btn variant="primary" disabled={!grant.plan || give.isPending} onClick={() => give.mutate(undefined)}>Grant</Btn>
                </div>
                <DataTable rows={subs.data} loading={subs.isLoading} error={subs.error} rowKey={(r) => r.id} empty="No subscriptions."
                  cols={[
                    { key: "p", head: "Plan", cell: (r) => r.plan_code },
                    { key: "s", head: "Status", cell: (r) => <Badge tone={r.status === "active" ? "green" : "gray"}>{r.status}</Badge> },
                    { key: "src", head: "Source", cell: (r) => r.source },
                    { key: "a", head: "Started", cell: (r) => fmtDate(r.started_at) },
                    { key: "u", head: "Until", cell: (r) => fmtDate(r.until) },
                    { key: "x", head: "", cell: (r) => r.status === "active" && <Btn variant="danger" onClick={() => confirm("Revoke this subscription?") && revoke.mutate(r.id)}>Revoke</Btn> },
                  ]} />
              </>
            )}
          </div>
        )}
      </div>
      <Drawer open={!!edit} onClose={() => setEdit(null)} width="max-w-xl" title={edit?.isNew ? "New plan" : "Edit plan"}
        footer={<>
          {edit && !edit.isNew && <Btn variant="danger" className="mr-auto" onClick={() => confirm("Delete plan?") && del.mutate(edit.form.code, { onSuccess: () => setEdit(null) })}>Delete</Btn>}
          <Btn onClick={() => setEdit(null)}>Cancel</Btn>
          <Btn variant="primary" disabled={save.isPending || !f?.code} onClick={() => save.mutate(edit!, { onSuccess: () => setEdit(null) })}>Save</Btn></>}>
        {f && (
          <div className="space-y-3">
            <Field label="Code"><Input value={f.code} disabled={!edit?.isNew} onChange={(e) => set({ code: e.target.value })} /></Field>
            <NamesEditor value={f.names} onChange={(names) => set({ names })} />
            <div className="grid grid-cols-3 gap-3">
              <Field label="Price (UZS)"><Input type="number" value={f.price_uzs} onChange={(e) => set({ price_uzs: Number(e.target.value) })} /></Field>
              <Field label="Period (months)"><Input type="number" min={1} value={f.period_months} onChange={(e) => set({ period_months: Number(e.target.value) })} /></Field>
              <Field label="Sort"><Input type="number" value={f.sort_order ?? 0} onChange={(e) => set({ sort_order: Number(e.target.value) })} /></Field>
            </div>
            <Field label="Features (comma separated)"><Input value={(f.features ?? []).join(", ")} onChange={(e) => set({ features: e.target.value.split(",").map((x) => x.trim()).filter(Boolean) })} /></Field>
            <Field label="Limits (JSON)"><JsonEditor value={f.limits} onChange={(limits) => set({ limits: limits as PlanCreate["limits"] })} rows={5} /></Field>
            <Check checked={f.active ?? true} onChange={(active) => set({ active })} label="Active (visible for purchase)" />
          </div>
        )}
      </Drawer>
    </>
  );
}
