"use client";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Badge, Field, Input, Select, Toolbar } from "@/components/ui/controls";
import { Pager, nextSort, type Order } from "@/components/ui/pager";
import { DataTable } from "@/components/ui/table";
import { labelers, type ActivitySort } from "@/lib/labelers";
import { users } from "@/lib/users";
import { fmtDate } from "@/lib/util";

/** Local date (YYYY-MM-DD) → ISO instant at start / end of that day. */
export const dayStart = (d: string) => (d ? new Date(`${d}T00:00:00`).toISOString() : undefined);
export const dayEnd = (d: string) => (d ? new Date(`${d}T23:59:59.999`).toISOString() : undefined);

const ACTIONS = ["claim", "label", "approve", "reject", "edit", "skip", "release"] as const;

export function ActivityPanel() {
  const [actor, setActor] = useState("");
  const [action, setAction] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [sort, setSort] = useState<{ key: ActivitySort; order: Order }>({ key: "created_at", order: "desc" });
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(25);
  const people = useQuery({ queryKey: ["admin-users", "labeler-options"], queryFn: () => users.list({ role: "labeler", size: 100 }) });
  const res = useQuery({
    queryKey: ["labeling-activity", actor, action, from, to, sort, page, size],
    queryFn: () => labelers.activity({ actor_id: actor, action, from: dayStart(from), to: dayEnd(to), sort: sort.key, order: sort.order, page, size }),
    placeholderData: keepPreviousData,
  });
  const f = <T,>(set: (v: T) => void) => (v: T) => { set(v); setPage(1); };
  return (
    <>
      <Toolbar>
        <Field label="Labeler"><Select value={actor} onChange={(e) => f(setActor)(e.target.value)}><option value="">All labelers</option>{people.data?.items.map((u) => <option key={u.id} value={u.id}>{u.display_name || u.email}</option>)}</Select></Field>
        <Field label="Action"><Select value={action} onChange={(e) => f(setAction)(e.target.value)}><option value="">All actions</option>{ACTIONS.map((a) => <option key={a} value={a}>{a}</option>)}</Select></Field>
        <Field label="From"><Input type="date" value={from} max={to || undefined} onChange={(e) => f(setFrom)(e.target.value)} /></Field>
        <Field label="To"><Input type="date" value={to} min={from || undefined} onChange={(e) => f(setTo)(e.target.value)} /></Field>
      </Toolbar>
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={res.data?.items} loading={res.isLoading} error={res.error} rowKey={(r) => r.id} empty="No activity for these filters."
          sort={sort} onSort={(k) => { setSort((s) => nextSort(s, k as ActivitySort)); setPage(1); }}
          cols={[
            { key: "t", head: "When", sortKey: "created_at", cell: (r) => fmtDate(r.created_at) },
            { key: "a", head: "Labeler", cell: (r) => r.actor_name ?? r.actor_id.slice(0, 8) },
            { key: "ac", head: "Action", sortKey: "action", cell: (r) => <Badge tone="blue">{r.action}</Badge> },
            { key: "q", head: "Question", cell: (r) => (r.question_id ? <code className="text-xs">{r.question_id.slice(0, 8)}</code> : "—") },
            { key: "d", head: "Duration", sortKey: "duration_ms", className: "text-right tabular-nums", cell: (r) => (r.duration_ms == null ? "—" : `${(r.duration_ms / 1000).toFixed(1)} s`) },
          ]} />
      </div>
      <Pager page={page} size={size} total={res.data?.total ?? 0} onPage={setPage} onSize={(s) => { setSize(s); setPage(1); }} />
    </>
  );
}
