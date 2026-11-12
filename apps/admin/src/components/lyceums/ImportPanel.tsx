"use client";
import { useT } from "@/lib/i18n";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { lyceums } from "@/lib/lyceums";
import { useAct } from "@/lib/catalog";
import { fieldErrors, fmtDate } from "@/lib/util";
import { Badge, Btn, Field, Input } from "@/components/ui/controls";
import { useConfirm } from "@/components/ui/confirm";
import { DataTable } from "@/components/ui/table";

const TONE: Record<string, "gray" | "green" | "red" | "blue" | "gold"> = { pending: "gray", running: "blue", succeeded: "green", partial: "gold", failed: "red" };

export function ImportPanel() {
  const t = useT();
  const [ask, confirmNode] = useConfirm();
  const [year, setYear] = useState(new Date().getFullYear());
  const runs = useQuery({ queryKey: ["lyceum-imports"], queryFn: () => lyceums.imports(), refetchInterval: 5000 });
  const start = useAct((y: number) => lyceums.start(y), [["lyceum-imports"]], t("admin.lyceums.importQueued"));
  const ie = fieldErrors(start.error);
  const maxYear = new Date().getFullYear() + 1;
  const yearErr = !Number.isInteger(year) || year < 2000 || year > maxYear ? t("admin.lyceums.yearRange", { min: 2000, max: maxYear }) : undefined;
  const [stat, setStat] = useState({ id: "", score: "" });
  const setScore = useAct((a: { id: string; score: number | null }) => lyceums.setPassingScore(a.id, a.score), [], t("admin.lyceums.passingScoreSaved"));
  const se = fieldErrors(setScore.error);
  return (
    <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">
      <div className="flex items-end gap-3 rounded-xl border border-line bg-white p-4">
        <Field label={t("admin.lyceums.admissionYear")} error={yearErr ?? ie.year}><Input type="number" min={2000} max={maxYear} value={year} onChange={(e) => setYear(Number(e.target.value))} /></Field>
        <Btn variant="primary" disabled={start.isPending || !!yearErr} onClick={() => ask({ title: t("admin.lyceums.importConfirm"), name: String(year), confirmLabel: t("admin.lyceums.importYear") }, () => start.mutate(year))}>{t("admin.lyceums.importYear")}</Btn>
      </div>
      <div className="flex items-end gap-3 rounded-xl border border-line bg-white p-4">
        <Field label={t("admin.lyceums.specialityStatId")} error={se.stat_id ?? se.id} hint={t("admin.lyceums.setTheManualPassing")}><Input value={stat.id} onChange={(e) => setStat({ ...stat, id: e.target.value })} /></Field>
        <Field label={t("admin.lyceums.passingScoreBlankClears")} error={se.passing_score ?? se.score}><Input type="number" step="0.1" value={stat.score} onChange={(e) => setStat({ ...stat, score: e.target.value })} /></Field>
        <Btn disabled={!stat.id || setScore.isPending} onClick={() => setScore.mutate({ id: stat.id, score: stat.score === "" ? null : Number(stat.score) })}>{t("admin.common.save")}</Btn>
      </div>
      {confirmNode}
      <DataTable rows={runs.data} loading={runs.isLoading} error={runs.error} rowKey={(r) => r.id} empty={t("admin.lyceums.noImportsYet")}
        cols={[
          { key: "y", head: t("admin.common.year"), cell: (r) => r.year },
          { key: "s", head: t("admin.common.status"), cell: (r) => <Badge tone={TONE[r.status] ?? "gray"}>{t(`admin.lyceums.status.${r.status}`)}</Badge> },
          { key: "l", head: t("admin.lyceums.lyceums"), cell: (r) => r.lyceums },
          { key: "st", head: t("admin.lyceums.statRows"), cell: (r) => r.stats },
          { key: "er", head: t("admin.lyceums.rowErrors"), cell: (r) => r.errors || "—" },
          { key: "c", head: t("admin.common.started"), cell: (r) => fmtDate(r.created_at) },
          { key: "f", head: t("admin.lyceums.finished"), cell: (r) => fmtDate(r.finished_at) },
          { key: "e", head: t("admin.common.error"), cell: (r) => <span className="text-red-deep">{r.error ?? ""}</span> },
        ]} />
    </div>
  );
}
