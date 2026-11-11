"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { users, type AdminUser } from "@/lib/users";
import { useAct } from "@/lib/catalog";
import { useAuth } from "@/lib/auth";
import { fmtDate } from "@/lib/util";
import { Badge, Btn, Check, Input, PageHeader } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";
import { Drawer } from "@/components/ui/overlay";
import { useToast } from "@dtmai/ui";

const ROLES = ["student", "editor", "admin"];

export default function UsersPage() {
  const { isAdmin } = useAuth();
  const toast = useToast();
  const [q, setQ] = useState("");
  const [term, setTerm] = useState("");
  const res = useQuery({ queryKey: ["admin-users", term], queryFn: () => users.search(term) });
  const [sel, setSel] = useState<AdminUser | null>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const save = useAct((a: { id: string; roles: string[] }) => users.setRoles(a.id, a.roles), [["admin-users"]], "Roles saved");
  return (
    <>
      <PageHeader title="Users" sub="Find users, copy their ID for grants, and manage staff roles." />
      <form className="flex gap-2 border-b border-line bg-white p-3" onSubmit={(e) => { e.preventDefault(); setTerm(q); }}>
        <Input className="w-80" placeholder="Search by email, name or Telegram ID" value={q} onChange={(e) => setQ(e.target.value)} /><Btn variant="primary" type="submit">Search</Btn>
        <span className="ml-auto self-center text-xs text-ink-soft">{res.data ? `${res.data.total} users` : ""}</span>
      </form>
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={res.data?.items} loading={res.isLoading} error={res.error} rowKey={(r) => r.id} onRow={(r) => { setSel(r); setRoles(r.roles); }}
          cols={[
            { key: "e", head: "Email", cell: (r) => r.email ?? "—" },
            { key: "n", head: "Name", cell: (r) => r.display_name ?? "—" },
            { key: "r", head: "Roles", cell: (r) => r.roles.map((x) => <Badge key={x} tone={x === "admin" ? "red" : x === "editor" ? "gold" : "gray"} className="mr-1">{x}</Badge>) },
            { key: "c", head: "Joined", cell: (r) => fmtDate(r.created_at) },
          ]} />
      </div>
      <Drawer open={!!sel} onClose={() => setSel(null)} width="max-w-md" title={sel?.email ?? sel?.display_name ?? "User"}
        footer={isAdmin && sel && <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate({ id: sel.id, roles }, { onSuccess: () => setSel(null) })}>Save roles</Btn>}>
        {sel && <div className="space-y-3">
          <div className="text-xs text-ink-soft">ID <code className="select-all">{sel.id}</code> <Btn variant="ghost" onClick={() => navigator.clipboard.writeText(sel.id).then(() => toast("Copied", "success"))}>Copy</Btn></div>
          {ROLES.map((r) => <Check key={r} label={r} checked={roles.includes(r)} onChange={(on) => setRoles((x) => (on ? [...x, r] : x.filter((y) => y !== r)))} />)}
        </div>}
      </Drawer>
    </>
  );
}
