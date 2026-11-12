"use client";
import { useT } from "@/lib/i18n";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { billing, type Plan, type PlanCreate } from "@/lib/billing";
import { useAct } from "@/lib/catalog";
import { fieldErrors, fmtDate, nm } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader, Select, Tabs } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";
import { Drawer } from "@/components/ui/overlay";
import { useConfirm } from "@/components/ui/confirm";
import { NamesEditor, cleanNames } from "@/components/ui/names";
import { JsonEditor } from "@/components/ui/json";

const blank: PlanCreate = { code: "", names: {}, price_uzs: 49000, period_months: 1, features: [], limits: {}, active: true, sort_order: 0 };
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default function BillingPage() {
  const t = useT();
  const [ask, confirmNode] = useConfirm();
  const [tab, setTab] = useState<"plans" | "grants">("plans");
  const plans = useQuery({ queryKey: ["billing-plans"], queryFn: billing.plans });
  const [edit, setEdit] = useState<{ isNew: boolean; form: PlanCreate } | null>(null);
  const save = useAct((e: { isNew: boolean; form: PlanCreate }) => {
    const form = { ...e.form, names: cleanNames(e.form.names) };
    if (e.isNew) return billing.createPlan(form);
    const { code, ...patch } = form;
    return billing.updatePlan(code, patch);
  }, [["billing-plans"]], t("admin.billing.planSaved"));
  const del = useAct((code: string) => billing.removePlan(code), [["billing-plans"]], t("admin.billing.planDeleted"));
  const f = edit?.form;
  const fe = fieldErrors(save.error);
  const set = (p: Partial<PlanCreate>) => setEdit((e) => e && { ...e, form: { ...e.form, ...p } });

  const [userId, setUserId] = useState("");
  const [lookup, setLookup] = useState("");
  const subs = useQuery({ queryKey: ["billing-subs", lookup], queryFn: () => billing.subscriptions(lookup), enabled: !!lookup });
  const [grant, setGrant] = useState({ plan: "", months: 1 });
  const give = useAct(() => billing.grant({ user_id: lookup, plan_code: grant.plan, months: grant.months }), [["billing-subs"]], t("admin.billing.granted"));
  const ge = fieldErrors(give.error);
  const revoke = useAct((id: string) => billing.revoke(id), [["billing-subs"]], t("admin.billing.revoked"));

  return (
    <>
      <PageHeader title={t("admin.billing.plansGrants")} sub={t("admin.billing.premiumPricingVariantsAnd")} actions={tab === "plans" ? <Btn variant="primary" onClick={() => setEdit({ isNew: true, form: blank })}>{t("admin.billing.newPlan")}</Btn> : undefined} />
      <div className="border-b border-line bg-white px-4"><Tabs value={tab} onChange={setTab} items={[{ id: "plans", label: t("admin.billing.plans") }, { id: "grants", label: t("admin.billing.grantsSubscriptions") }]} /></div>
      <div className="min-h-0 flex-1 overflow-auto">
        {tab === "plans" ? (
          <DataTable rows={plans.data} loading={plans.isLoading} error={plans.error} rowKey={(r) => r.code} onRow={(p: Plan) => setEdit({ isNew: false, form: { code: p.code, names: p.names, price_uzs: p.price_uzs, period_months: p.period_months, features: p.features, limits: p.limits, active: p.active, sort_order: p.sort_order } })}
            cols={[
              { key: "c", head: t("admin.common.code"), cell: (r) => <code>{r.code}</code> },
              { key: "n", head: t("admin.common.name"), cell: (r) => nm(r.names) },
              { key: "p", head: t("admin.billing.priceUzs"), cell: (r) => r.price_uzs.toLocaleString() },
              { key: "m", head: t("admin.billing.months"), cell: (r) => r.period_months },
              { key: "f", head: t("admin.billing.features"), cell: (r) => r.features.join(", ") },
              { key: "a", head: t("admin.common.state"), cell: (r) => <Badge tone={r.active ? "green" : "gray"}>{r.active ? t("admin.common.active") : t("admin.topics.inactive")}</Badge> },
            ]} />
        ) : (
          <div className="space-y-4 p-4">
            <div className="flex items-end gap-3 rounded-xl border border-line bg-white p-4">
              <Field label={t("admin.billing.userId")} hint={t("admin.billing.uuidFromTheUsers")} error={userId && !UUID_RE.test(userId) ? t("admin.error.field.uuid_parsing") : undefined}><Input className="w-full sm:w-80" value={userId} onChange={(e) => setUserId(e.target.value.trim())} /></Field>
              <Btn variant="primary" disabled={!UUID_RE.test(userId)} onClick={() => setLookup(userId)}>{t("admin.billing.loadSubscriptions")}</Btn>
            </div>
            {lookup && (
              <>
                <div className="flex items-end gap-3 rounded-xl border border-line bg-white p-4">
                  <Field label={t("admin.billing.grantPlan")} error={ge.plan_code}><Select value={grant.plan} onChange={(e) => setGrant({ ...grant, plan: e.target.value })}><option value="">—</option>{plans.data?.map((p) => <option key={p.code} value={p.code}>{p.code}</option>)}</Select></Field>
                  <Field label={t("admin.billing.months")} error={ge.months}><Input type="number" min={1} max={36} value={grant.months} onChange={(e) => setGrant({ ...grant, months: Number(e.target.value) })} /></Field>
                  <Btn variant="primary" disabled={!grant.plan || grant.months < 1 || give.isPending} onClick={() => give.mutate(undefined)}>{t("admin.billing.grant")}</Btn>
                </div>
                <DataTable rows={subs.data} loading={subs.isLoading} error={subs.error} rowKey={(r) => r.id} empty={t("admin.billing.noSubscriptions")}
                  cols={[
                    { key: "p", head: t("admin.billing.plan"), cell: (r) => r.plan_code },
                    { key: "s", head: t("admin.common.status"), cell: (r) => <Badge tone={r.status === "active" ? "green" : "gray"}>{t(`admin.billing.status.${r.status}`)}</Badge> },
                    { key: "src", head: t("admin.common.source"), cell: (r) => r.source },
                    { key: "a", head: t("admin.common.started"), cell: (r) => fmtDate(r.started_at) },
                    { key: "u", head: t("admin.billing.until"), cell: (r) => fmtDate(r.until) },
                    { key: "x", head: "", cell: (r) => r.status === "active" && <Btn variant="danger" onClick={() => ask({ title: t("admin.billing.revokeThisSubscription"), name: r.plan_code, danger: true, confirmLabel: t("admin.billing.revoke") }, () => revoke.mutate(r.id))}>{t("admin.billing.revoke")}</Btn> },
                  ]} />
              </>
            )}
          </div>
        )}
      </div>
      <Drawer open={!!edit} onClose={() => setEdit(null)} width="max-w-xl" title={edit?.isNew ? t("admin.billing.newPlan") : t("admin.billing.editPlan")}
        footer={<>
          {edit && !edit.isNew && <Btn variant="danger" className="mr-auto" onClick={() => ask({ title: t("admin.billing.deletePlan"), name: edit.form.code, danger: true, confirmLabel: t("admin.common.delete") }, () => del.mutate(edit.form.code, { onSuccess: () => setEdit(null) }))}>{t("admin.common.delete")}</Btn>}
          <Btn onClick={() => setEdit(null)}>{t("admin.common.cancel")}</Btn>
          <Btn variant="primary" disabled={save.isPending || !f?.code} onClick={() => save.mutate(edit!, { onSuccess: () => setEdit(null) })}>{t("admin.common.save")}</Btn></>}>
        {f && (
          <div className="space-y-3">
            <Field label={t("admin.common.code")} error={fe.code}><Input value={f.code} disabled={!edit?.isNew} onChange={(e) => set({ code: e.target.value })} /></Field>
            <NamesEditor value={f.names} onChange={(names) => set({ names })} error={fe.names} />
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Field label={t("admin.billing.priceUzs")} error={fe.price_uzs}><Input type="number" value={f.price_uzs} onChange={(e) => set({ price_uzs: Number(e.target.value) })} /></Field>
              <Field label={t("admin.billing.periodMonths")} error={fe.period_months}><Input type="number" min={1} value={f.period_months} onChange={(e) => set({ period_months: Number(e.target.value) })} /></Field>
              <Field label={t("admin.billing.sort")} error={fe.sort_order}><Input type="number" value={f.sort_order ?? 0} onChange={(e) => set({ sort_order: Number(e.target.value) })} /></Field>
            </div>
            <Field label={t("admin.billing.featuresCommaSeparated")} error={fe.features}><Input value={(f.features ?? []).join(", ")} onChange={(e) => set({ features: e.target.value.split(",").map((x) => x.trim()).filter(Boolean) })} /></Field>
            <Field label={t("admin.billing.limitsJson")} error={fe.limits}><JsonEditor value={f.limits} onChange={(limits) => set({ limits: limits as PlanCreate["limits"] })} rows={5} /></Field>
            <Check checked={f.active ?? true} onChange={(active) => set({ active })} label={t("admin.billing.activeVisibleForPurchase")} />
          </div>
        )}
      </Drawer>
      {confirmNode}
    </>
  );
}
