"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Badge, Field, Input, Toolbar } from "@/components/ui/controls";
import { nextSort, type Order } from "@/components/ui/pager";
import { DataTable } from "@/components/ui/table";
import { labelers, type LeaderSort } from "@/lib/labelers";
import { dayEnd, dayStart } from "./ActivityPanel";
import { fmtDate } from "@/lib/util";

export function LeaderboardPanel() {
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [sort, setSort] = useState<{ key: LeaderSort; order: Order }>({ key: "labeled", order: "desc" });
  const res = useQuery({ queryKey: ["labeling-leaderboard", from, to, sort], queryFn: () => labelers.leaderboard({ from: dayStart(from), to: dayEnd(to), sort: sort.key, order: sort.order }) });
  return (
    <>
      <Toolbar>
        <Field label="From"><Input type="date" value={from} max={to || undefined} onChange={(e) => setFrom(e.target.value)} /></Field>
        <Field label="To"><Input type="date" value={to} min={from || undefined} onChange={(e) => setTo(e.target.value)} /></Field>
      </Toolbar>
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={res.data} loading={res.isLoading} error={res.error} rowKey={(r) => r.actor_id} empty="No labeling in this period."
          sort={sort} onSort={(k) => setSort((s) => nextSort(s, k as LeaderSort))}
          cols={[
            { key: "#", head: "#", className: "w-10 tabular-nums", cell: (_r, i) => i + 1 },
            { key: "n", head: "Labeler", cell: (r) => <span className="font-extrabold">{r.actor_name ?? r.actor_id.slice(0, 8)}{r.is_system && <Badge className="ml-1" tone="blue">system</Badge>}</span> },
            { key: "l", head: "Labeled", sortKey: "labeled", className: "text-right tabular-nums", cell: (r) => r.labeled },
            { key: "a", head: "Approved", sortKey: "approved", className: "text-right tabular-nums", cell: (r) => r.approved },
            { key: "r", head: "Rejected", sortKey: "rejected", className: "text-right tabular-nums", cell: (r) => r.rejected },
            { key: "d", head: "Avg time", sortKey: "avg_duration", className: "text-right tabular-nums", cell: (r) => (r.avg_duration_ms == null ? "—" : `${(r.avg_duration_ms / 1000).toFixed(1)} s`) },
            { key: "t", head: "Last active", cell: (r) => fmtDate(r.last_active_at) },
          ]} />
      </div>
    </>
  );
}
