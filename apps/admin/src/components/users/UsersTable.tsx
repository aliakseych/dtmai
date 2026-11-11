"use client";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Badge, Field, Input, Select, Toolbar } from "@/components/ui/controls";
import { Pager, nextSort, type Order } from "@/components/ui/pager";
import { DataTable } from "@/components/ui/table";
import { users, type AdminUser, type UserSort, type UserStatus } from "@/lib/users";
import { fmtDate } from "@/lib/util";

const roleTone = (r: string) => (r === "admin" ? "red" : r === "student" ? "gray" : "gold");

/** Server-paged, searchable, filterable, sortable user table. `roles` fixes the role filter choices; `allowAnyRole` adds "All roles". */
export function UsersTable({ roles, role: initialRole, allowAnyRole, onOpen, selected, toolbarExtra, queryKey }: {
  roles: readonly string[]; role: string; allowAnyRole: boolean; onOpen: (u: AdminUser) => void; selected?: string | null; toolbarExtra?: React.ReactNode; queryKey: string;
}) {
  const [q, setQ] = useState("");
  const [term, setTerm] = useState("");
  const [role, setRole] = useState(initialRole);
  const [status, setStatus] = useState<"" | UserStatus>("");
  const [sort, setSort] = useState<{ key: UserSort; order: Order }>({ key: "created_at", order: "desc" });
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(25);
  useEffect(() => {
    const t = setTimeout(() => { setTerm(q.trim()); setPage(1); }, 300);
    return () => clearTimeout(t);
  }, [q]);
  const res = useQuery({
    queryKey: ["admin-users", queryKey, term, role, status, sort, page, size],
    queryFn: () => users.list({ q: term, role, status: status || undefined, sort: sort.key, order: sort.order, page, size }),
    placeholderData: keepPreviousData,
  });
  const reset = <T,>(set: (v: T) => void) => (v: T) => { set(v); setPage(1); };
  const onSort = (k: string) => { setSort((s) => nextSort(s, k as UserSort)); setPage(1); };
  return (
    <>
      <Toolbar>
        <Field label="Search"><Input className="w-64 max-w-full" type="search" placeholder="Email, name or Telegram" value={q} onChange={(e) => setQ(e.target.value)} /></Field>
        <Field label="Role">
          <Select value={role} onChange={(e) => reset(setRole)(e.target.value)}>
            {allowAnyRole && <option value="">All roles</option>}
            {roles.map((r) => <option key={r} value={r}>{r}</option>)}
          </Select>
        </Field>
        <Field label="Status">
          <Select value={status} onChange={(e) => reset(setStatus)(e.target.value as "" | UserStatus)}>
            <option value="">Any status</option><option value="active">Active</option><option value="disabled">Disabled</option>
          </Select>
        </Field>
        <div className="ml-auto flex items-center gap-2">{toolbarExtra}</div>
      </Toolbar>
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={res.data?.items} loading={res.isLoading} error={res.error} rowKey={(r) => r.id} onRow={onOpen} selected={selected}
          empty="No users match these filters." sort={sort} onSort={onSort}
          cols={[
            { key: "n", head: "Name", cell: (r) => <span className="font-extrabold">{r.display_name || "—"}{r.is_system && <Badge className="ml-1" tone="blue">system</Badge>}</span> },
            { key: "e", head: "Email / login", sortKey: "email", cell: (r) => r.email ?? (r.telegram_username ? `@${r.telegram_username}` : "—") },
            { key: "r", head: "Roles", cell: (r) => r.roles.map((x) => <Badge key={x} tone={roleTone(x)} className="mr-1">{x}</Badge>) },
            { key: "s", head: "Status", cell: (r) => <Badge tone={r.status === "active" ? "green" : "red"}>{r.status}</Badge> },
            { key: "l", head: "Last seen", sortKey: "last_seen_at", cell: (r) => fmtDate(r.last_seen_at) },
            { key: "c", head: "Joined", sortKey: "created_at", cell: (r) => fmtDate(r.created_at) },
          ]} />
      </div>
      <Pager page={page} size={size} total={res.data?.total ?? 0} onPage={setPage} onSize={(s) => { setSize(s); setPage(1); }} />
    </>
  );
}
