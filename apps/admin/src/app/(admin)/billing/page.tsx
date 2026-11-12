"use client";
import { useEnum, useT } from "@/lib/i18n";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { users, type AdminUser } from "@/lib/users";
import { EmptyState } from "@dtmai/ui";
import { billing, type Plan, type PlanCreate } from "@/lib/billing";
import { useAct } from "@/lib/catalog";
import { fieldErrors, fmtDate, fmtNum, nm } from "@/lib/util";
import { Badge, Btn, Check, Field, Input, PageHeader, Select, Tabs } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";
import { Drawer } from "@/components/ui/overlay";
import { useConfirm } from "@/components/ui/confirm";
import { NamesEditor, cleanNames } from "@/components/ui/names";
import { JsonEditor } from "@/components/ui/json";

const blank: PlanCreate = { code: "", names: {}, price_uzs: 49000, period_months: 1, features: [], limits: {}, active: true, sort_order: 0 };

export default function BillingPage() {
  const t = useT();
  const en = useEnum();
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

  const [q, setQ] = useState("");
  const [term, setTerm] = useState("");
  const found = useQuery({ queryKey: ["billing-user-search", term], queryFn: () => users.list({ q: term, size: 8 }), enabled: !!term });
  const [picked, setPicked] = useState<AdminUser | null>(null);
  const lookup = picked?.id ?? "";
  const warnings = (u: AdminUser) => [u.status === "disabled" ? t("admin.billing.warnDisabled") : "", !u.email || u.roles.includes("guest" as never) ? t("admin.billing.warnGuest") : ""].filter(Boolean);
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
              { key: "p", head: t("admin.billing.priceUzs"), cell: (r) => t("admin.billing.priceFmt", { n: fmtNum(r.price_uzs) }) },
              { key: "m", head: t("admin.billing.months"), cell: (r) => r.period_months },
              { key: "f", head: t("admin.billing.features"), cell: (r) => r.features.map((x) => en("planFeature", x)).join(", ") },
              { key: "a", head: t("admin.common.state"), cell: (r) => <Badge tone={r.active ? "green" : "gray"}>{r.active ? t("admin.common.active") : t("admin.topics.inactive")}</Badge> },
            ]} />
        ) : (
          <div className="space-y-4 p-4">
            <div className="space-y-3 rounded-xl border border-line bg-white p-4">
              <form className="flex items-end gap-3" onSubmit={(e) => { e.preventDefault(); setTerm(q.trim()); }}>
                <Field label={t("admin.billing.findUser")} hint={t("admin.billing.findUserHint")}><Input className="w-full sm:w-80" value={q} onChange={(e) => setQ(e.target.value)} /></Field>
                <Btn variant="primary" type="submit" disabled={!q.trim()}>{t("admin.billing.searchUser")}</Btn>
              </form>
              {term && !picked && (found.data?.items.length ? (
                <ul className="divide-y divide-line rounded-xl border border-line">
                  {found.data.items.map((u) => (
                    <li key={u.id}><button type="button" onClick={() => setPicked(u)} className="flex w-full flex-wrap items-center justify-between gap-2 px-3 py-2 text-left text-sm hover:bg-snow">
                      <span><b>{u.display_name}</b> · {u.email ?? <code>{u.id.slice(0, 8)}</code>} · <span className="text-ink-soft">{fmtDate(u.created_at)}</span></span>
                      <span className="flex gap-1"><Badge tone={u.status === "active" ? "green" : "gray"}>{en("userStatus", u.status)}</Badge>{u.roles.map((r) => <Badge key={r} tone="gray">{en("role", r)}</Badge>)}</span>
                    </button></li>
                  ))}
                  {found.data.total > found.data.items.length && <li className="px-3 py-2 text-xs font-bold text-ink-soft">{t("admin.billing.moreResults", { n: found.data.total - found.data.items.length })}</li>}
                </ul>
              ) : found.isLoading ? null : <EmptyState compact title={t("admin.billing.noUserFound")} />)}
              {picked && (
                <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-snow p-3 text-sm">
                  <span><b>{picked.display_name}</b> · {picked.email ?? "—"} <Badge tone={picked.status === "active" ? "green" : "gray"}>{en("userStatus", picked.status)}</Badge></span>
                  <Btn onClick={() => setPicked(null)}>{t("admin.billing.changeUser")}</Btn>
                </div>
              )}
              {picked && warnings(picked).map((w) => <p key={w} role="alert" className="text-sm font-bold text-red-deep">{w}</p>)}
            </div>
            {lookup && (
              <>
                <div className="flex items-end gap-3 rounded-xl border border-line bg-white p-4">
                  <Field label={t("admin.billing.grantPlan")} error={ge.plan_code}><Select value={grant.plan} onChange={(e) => setGrant({ ...grant, plan: e.target.value })}><option value="">—</option>{plans.data?.map((p) => <option key={p.code} value={p.code}>{nm(p.names)} · {p.code}</option>)}</Select></Field>
                  <Field label={t("admin.billing.months")} error={ge.months}><Input type="number" min={1} max={36} value={grant.months} onChange={(e) => setGrant({ ...grant, months: Number(e.target.value) })} /></Field>
                  <Btn variant="primary" disabled={!grant.plan || picked?.status === "disabled" || grant.months < 1 || give.isPending} onClick={() => { const w = picked ? warnings(picked) : []; ask({ title: t("admin.billing.confirmGrant"), name: `${picked?.display_name} · ${picked?.email ?? "—"}`, body: <div className="space-y-1"><p className="font-bold">{nm(plans.data?.find((p) => p.code === grant.plan)?.names) } · {grant.plan} · {grant.months} {t("admin.billing.months")}</p>{w.map((x) => <p key={x} className="font-bold text-red-deep">{x}</p>)}</div>, danger: w.length > 0, confirmLabel: t("admin.billing.grant") }, () => give.mutate(undefined)); }}>{t("admin.billing.grant")}</Btn>
                </div>
                <DataTable rows={subs.data} loading={subs.isLoading} error={subs.error} rowKey={(r) => r.id} empty={t("admin.billing.noSubscriptions")}
                  cols={[
                    { key: "p", head: t("admin.billing.plan"), cell: (r) => r.plan_code },
                    { key: "s", head: t("admin.common.status"), cell: (r) => <Badge tone={r.status === "active" ? "green" : "gray"}>{t(`admin.billing.status.${r.status}`)}</Badge> },
                    { key: "src", head: t("admin.common.source"), cell: (r) => en("subSource", r.source) },
                    { key: "a", head: t("admin.common.started"), cell: (r) => fmtDate(r.started_at) },
                    { key: "u", head: t("admin.billing.until"), cell: (r) => fmtDate(r.until) },
                    { key: "x", head: "", cell: (r) => r.status === "active" && <Btn variant="danger" onClick={() => ask({ title: t("admin.billing.revokeThisSubscription"), name: r.plan_code, danger: true, confirmLabel: t("admin.billing.revokeSubscription"), cancelLabel: t("admin.billing.keepSubscription") }, () => revoke.mutate(r.id))}>{t("admin.billing.revoke")}</Btn> },
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
