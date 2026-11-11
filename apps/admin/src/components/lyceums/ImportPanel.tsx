"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { lyceums } from "@/lib/lyceums";
import { useAct } from "@/lib/catalog";
import { fmtDate } from "@/lib/util";
import { Badge, Btn, Field, Input } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";

const TONE: Record<string, "gray" | "green" | "red" | "blue" | "gold"> = { queued: "gray", running: "blue", done: "green", failed: "red" };

export function ImportPanel() {
  const [year, setYear] = useState(new Date().getFullYear());
  const runs = useQuery({ queryKey: ["lyceum-imports"], queryFn: () => lyceums.imports(), refetchInterval: 5000 });
  const start = useAct((y: number) => lyceums.start(y), [["lyceum-imports"]], "Import queued");
  const [stat, setStat] = useState({ id: "", score: "" });
  const setScore = useAct((a: { id: string; score: number | null }) => lyceums.setPassingScore(a.id, a.score), [], "Passing score saved");
  return (
    <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">
      <div className="flex items-end gap-3 rounded-xl border border-line bg-white p-4">
        <Field label="Admission year"><Input type="number" value={year} onChange={(e) => setYear(Number(e.target.value))} /></Field>
        <Btn variant="primary" disabled={start.isPending} onClick={() => start.mutate(year)}>Import year</Btn>
      </div>
      <div className="flex items-end gap-3 rounded-xl border border-line bg-white p-4">
        <Field label="Speciality stat ID" hint="Set the manual passing score of one imported speciality row."><Input value={stat.id} onChange={(e) => setStat({ ...stat, id: e.target.value })} /></Field>
        <Field label="Passing score (blank clears)"><Input type="number" step="0.1" value={stat.score} onChange={(e) => setStat({ ...stat, score: e.target.value })} /></Field>
        <Btn disabled={!stat.id || setScore.isPending} onClick={() => setScore.mutate({ id: stat.id, score: stat.score === "" ? null : Number(stat.score) })}>Save</Btn>
      </div>
      <DataTable rows={runs.data} loading={runs.isLoading} error={runs.error} rowKey={(r) => r.id} empty="No imports yet."
        cols={[
          { key: "y", head: "Year", cell: (r) => r.year },
          { key: "s", head: "Status", cell: (r) => <Badge tone={TONE[r.status] ?? "gray"}>{r.status}</Badge> },
          { key: "l", head: "Lyceums", cell: (r) => r.lyceums },
          { key: "st", head: "Stat rows", cell: (r) => r.stats },
          { key: "er", head: "Row errors", cell: (r) => r.errors || "—" },
          { key: "c", head: "Started", cell: (r) => fmtDate(r.created_at) },
          { key: "f", head: "Finished", cell: (r) => fmtDate(r.finished_at) },
          { key: "e", head: "Error", cell: (r) => <span className="text-red-deep">{r.error ?? ""}</span> },
        ]} />
    </div>
  );
}
