"use client";
import { useT } from "@/lib/i18n";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { lyceums } from "@/lib/lyceums";
import { useAct } from "@/lib/catalog";
import { Badge, Btn, Field, Input, Select } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";

const KEY = [["lyceum-seed-matches"], ["lyceum-admission-detail"]] as const;

/** Seed-document ↔ lyceum matching (unmatched rows first) and manual plan / contact editing. */
export function AdmissionPanel() {
  const t = useT();
  const matches = useQuery({ queryKey: ["lyceum-seed-matches"], queryFn: () => lyceums.seedMatches() });
  const all = useQuery({ queryKey: ["lyceum-admission-list"], queryFn: () => lyceums.list() });
  const setMatch = useAct(
    (a: { kind: "plan" | "contact"; ref: number; id: string | null }) => lyceums.setSeedMatch(a.kind, a.ref, a.id),
    KEY, t("admin.lyceums.matchSaved"),
  );
  const [target, setTarget] = useState("");
  const detail = useQuery({
    queryKey: ["lyceum-admission-detail", target], enabled: !!target, queryFn: () => lyceums.detail(target),
  });
  const [row, setRow] = useState({ year: 2026, code: "", language: "", uz: "0", ru: "0", qq: "0" });
  const savePlan = useAct(
    () => lyceums.putPlanRow(target, {
      year: row.year, direction_code: row.code, language_name: row.language || null,
      seats_uz: Number(row.uz), seats_ru: Number(row.ru), seats_qq: Number(row.qq),
    }),
    KEY, t("admin.lyceums.planRowSaved"),
  );
  const delRow = useAct(
    (a: { year: number; code: string; lang: string | null }) => lyceums.deletePlanRow(target, a.year, a.code, a.lang),
    KEY, t("admin.lyceums.planRowDeleted"),
  );
  const [contact, setContact] = useState({ phones: "", telegram: "" });
  const saveContact = useAct(
    () => lyceums.putContact(target, contact.phones.split(/[\s,;]+/).filter(Boolean), contact.telegram || null),
    KEY, t("admin.lyceums.contactsSaved"),
  );
  const options = all.data ?? [];
  const unmatched = (matches.data ?? []).filter((m) => !m.lyceum_id).length;

  return (
    <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">
      <p className="text-ink-soft">
        {unmatched > 0 ? t("admin.lyceums.seedRowsUnmatched", { n: unmatched }) : t("admin.lyceums.allSeedRowsAre")}
      </p>
      <DataTable rows={matches.data} loading={matches.isLoading} error={matches.error} rowKey={(m) => `${m.kind}-${m.ref}`} empty={t("admin.lyceums.runPythonMApp")}
        cols={[
          { key: "k", head: t("admin.lyceums.document"), cell: (m) => (m.kind === "plan" ? t("admin.lyceums.admissionPlan") : t("admin.lyceums.contacts")) },
          { key: "n", head: "#", cell: (m) => m.ref },
          { key: "nm", head: t("admin.lyceums.nameInDocument"), cell: (m) => m.name },
          { key: "l", head: t("admin.lyceums.lyceum"), cell: (m) => (
            <Select value={m.lyceum_id ?? ""} onChange={(e) => setMatch.mutate({ kind: m.kind, ref: m.ref, id: e.target.value || null })}>
              <option value="">{t("admin.lyceums.unmatched2")}</option>
              {options.map((o) => <option key={o.id} value={o.id}>{o.names.uz}</option>)}
            </Select>
          ) },
          { key: "s", head: t("admin.common.source"), cell: (m) => (m.lyceum_id ? <Badge tone={m.source === "admin" ? "blue" : "green"}>{m.source}</Badge> : <Badge tone="red">{t("admin.lyceums.unmatched")}</Badge>) },
        ]} />

      <div className="space-y-3 rounded-xl border border-line bg-white p-4">
        <Field label={t("admin.lyceums.lyceumToEdit")}>
          <Select value={target} onChange={(e) => setTarget(e.target.value)}>
            <option value="">{t("admin.lyceums.choose")}</option>
            {options.map((o) => <option key={o.id} value={o.id}>{o.names.uz}</option>)}
          </Select>
        </Field>
        {target && detail.data && (
          <>
            <DataTable rows={detail.data.admission.plan} loading={false} error={null} rowKey={(r) => `${r.direction_code}-${r.language_name ?? ""}`} empty={t("admin.lyceums.noPlanRows")}
              cols={[
                { key: "c", head: t("admin.common.direction"), cell: (r) => r.direction_code },
                { key: "g", head: t("admin.common.language"), cell: (r) => r.language_name ?? "—" },
                { key: "u", head: t("admin.common.uz"), cell: (r) => r.seats_uz },
                { key: "r", head: t("admin.common.ru"), cell: (r) => r.seats_ru },
                { key: "q", head: t("admin.lyceums.qq"), cell: (r) => r.seats_qq },
                { key: "t", head: t("admin.lyceums.total"), cell: (r) => r.seats_total },
                { key: "x", head: t("admin.lyceums.ratio"), cell: (r) => r.ratio ?? "—" },
                { key: "s", head: t("admin.common.source"), cell: (r) => <Badge tone={r.source === "admin" ? "blue" : "gray"}>{r.source}</Badge> },
                { key: "d", head: "", cell: (r) => (
                  <Btn variant="danger" onClick={() => delRow.mutate({ year: detail.data!.admission.year ?? row.year, code: r.direction_code, lang: r.language_name })}>{t("admin.common.delete")}</Btn>
                ) },
              ]} />
            <div className="flex flex-wrap items-end gap-3">
              <Field label={t("admin.common.year")}><Input type="number" value={row.year} onChange={(e) => setRow({ ...row, year: Number(e.target.value) })} /></Field>
              <Field label={t("admin.lyceums.directionCode")}><Input value={row.code} onChange={(e) => setRow({ ...row, code: e.target.value })} /></Field>
              <Field label={t("admin.lyceums.languageOptional")}><Input value={row.language} onChange={(e) => setRow({ ...row, language: e.target.value })} /></Field>
              <Field label={t("admin.lyceums.seatsUz")}><Input type="number" min={0} value={row.uz} onChange={(e) => setRow({ ...row, uz: e.target.value })} /></Field>
              <Field label={t("admin.lyceums.seatsRu")}><Input type="number" min={0} value={row.ru} onChange={(e) => setRow({ ...row, ru: e.target.value })} /></Field>
              <Field label={t("admin.lyceums.seatsQq")}><Input type="number" min={0} value={row.qq} onChange={(e) => setRow({ ...row, qq: e.target.value })} /></Field>
              <Btn variant="primary" disabled={!row.code || savePlan.isPending} onClick={() => savePlan.mutate(undefined)}>{t("admin.lyceums.savePlanRow")}</Btn>
            </div>
            <div className="flex flex-wrap items-end gap-3">
              <Field label={t("admin.lyceums.phones")} hint={t("admin.lyceums.currentPhones", { v: detail.data.admission.contact?.phones.join(", ") || t("admin.common.none") })}>
                <Input value={contact.phones} onChange={(e) => setContact({ ...contact, phones: e.target.value })} />
              </Field>
              <Field label={t("admin.lyceums.telegram")} hint={detail.data.admission.contact?.telegram ?? undefined}>
                <Input value={contact.telegram} onChange={(e) => setContact({ ...contact, telegram: e.target.value })} />
              </Field>
              <Btn variant="primary" disabled={saveContact.isPending} onClick={() => saveContact.mutate(undefined)}>{t("admin.lyceums.saveContacts")}</Btn>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
