"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { lyceums } from "@/lib/lyceums";
import { useAct } from "@/lib/catalog";
import { Badge, Btn, Field, Input, Select } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";

const KEY = [["lyceum-seed-matches"], ["lyceum-admission-detail"]] as const;

/** Seed-document ↔ lyceum matching (unmatched rows first) and manual plan / contact editing. */
export function AdmissionPanel() {
  const matches = useQuery({ queryKey: ["lyceum-seed-matches"], queryFn: () => lyceums.seedMatches() });
  const all = useQuery({ queryKey: ["lyceum-admission-list"], queryFn: () => lyceums.list() });
  const setMatch = useAct(
    (a: { kind: "plan" | "contact"; ref: number; id: string | null }) => lyceums.setSeedMatch(a.kind, a.ref, a.id),
    KEY, "Match saved",
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
    KEY, "Plan row saved",
  );
  const delRow = useAct(
    (a: { year: number; code: string; lang: string | null }) => lyceums.deletePlanRow(target, a.year, a.code, a.lang),
    KEY, "Plan row deleted",
  );
  const [contact, setContact] = useState({ phones: "", telegram: "" });
  const saveContact = useAct(
    () => lyceums.putContact(target, contact.phones.split(/[\s,;]+/).filter(Boolean), contact.telegram || null),
    KEY, "Contacts saved",
  );
  const options = all.data ?? [];
  const unmatched = (matches.data ?? []).filter((m) => !m.lyceum_id).length;

  return (
    <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">
      <p className="text-ink-soft">
        {unmatched > 0 ? `${unmatched} seed rows are not matched to a lyceum. Pick one manually.` : "All seed rows are matched."}
      </p>
      <DataTable rows={matches.data} loading={matches.isLoading} error={matches.error} rowKey={(m) => `${m.kind}-${m.ref}`} empty="Run `python -m app import-lyceum-admission`."
        cols={[
          { key: "k", head: "Document", cell: (m) => (m.kind === "plan" ? "Admission plan" : "Contacts") },
          { key: "n", head: "#", cell: (m) => m.ref },
          { key: "nm", head: "Name in document", cell: (m) => m.name },
          { key: "l", head: "Lyceum", cell: (m) => (
            <Select value={m.lyceum_id ?? ""} onChange={(e) => setMatch.mutate({ kind: m.kind, ref: m.ref, id: e.target.value || null })}>
              <option value="">— unmatched —</option>
              {options.map((o) => <option key={o.id} value={o.id}>{o.names.uz}</option>)}
            </Select>
          ) },
          { key: "s", head: "Source", cell: (m) => (m.lyceum_id ? <Badge tone={m.source === "admin" ? "blue" : "green"}>{m.source}</Badge> : <Badge tone="red">unmatched</Badge>) },
        ]} />

      <div className="space-y-3 rounded-xl border border-line bg-white p-4">
        <Field label="Lyceum to edit">
          <Select value={target} onChange={(e) => setTarget(e.target.value)}>
            <option value="">— choose —</option>
            {options.map((o) => <option key={o.id} value={o.id}>{o.names.uz}</option>)}
          </Select>
        </Field>
        {target && detail.data && (
          <>
            <DataTable rows={detail.data.admission.plan} loading={false} error={null} rowKey={(r) => `${r.direction_code}-${r.language_name ?? ""}`} empty="No plan rows."
              cols={[
                { key: "c", head: "Direction", cell: (r) => r.direction_code },
                { key: "g", head: "Language", cell: (r) => r.language_name ?? "—" },
                { key: "u", head: "uz", cell: (r) => r.seats_uz },
                { key: "r", head: "ru", cell: (r) => r.seats_ru },
                { key: "q", head: "qq", cell: (r) => r.seats_qq },
                { key: "t", head: "Total", cell: (r) => r.seats_total },
                { key: "x", head: "Ratio", cell: (r) => r.ratio ?? "—" },
                { key: "s", head: "Source", cell: (r) => <Badge tone={r.source === "admin" ? "blue" : "gray"}>{r.source}</Badge> },
                { key: "d", head: "", cell: (r) => (
                  <Btn variant="danger" onClick={() => delRow.mutate({ year: detail.data!.admission.year ?? row.year, code: r.direction_code, lang: r.language_name })}>Delete</Btn>
                ) },
              ]} />
            <div className="flex flex-wrap items-end gap-3">
              <Field label="Year"><Input type="number" value={row.year} onChange={(e) => setRow({ ...row, year: Number(e.target.value) })} /></Field>
              <Field label="Direction code"><Input value={row.code} onChange={(e) => setRow({ ...row, code: e.target.value })} /></Field>
              <Field label="Language (optional)"><Input value={row.language} onChange={(e) => setRow({ ...row, language: e.target.value })} /></Field>
              <Field label="Seats uz"><Input type="number" min={0} value={row.uz} onChange={(e) => setRow({ ...row, uz: e.target.value })} /></Field>
              <Field label="Seats ru"><Input type="number" min={0} value={row.ru} onChange={(e) => setRow({ ...row, ru: e.target.value })} /></Field>
              <Field label="Seats qq"><Input type="number" min={0} value={row.qq} onChange={(e) => setRow({ ...row, qq: e.target.value })} /></Field>
              <Btn variant="primary" disabled={!row.code || savePlan.isPending} onClick={() => savePlan.mutate(undefined)}>Save plan row</Btn>
            </div>
            <div className="flex flex-wrap items-end gap-3">
              <Field label="Phones" hint={`Current: ${detail.data.admission.contact?.phones.join(", ") || "none"}`}>
                <Input value={contact.phones} onChange={(e) => setContact({ ...contact, phones: e.target.value })} />
              </Field>
              <Field label="Telegram" hint={detail.data.admission.contact?.telegram ?? undefined}>
                <Input value={contact.telegram} onChange={(e) => setContact({ ...contact, telegram: e.target.value })} />
              </Field>
              <Btn variant="primary" disabled={saveContact.isPending} onClick={() => saveContact.mutate(undefined)}>Save contacts</Btn>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
