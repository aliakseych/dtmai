"use client";
import { useQuery } from "@tanstack/react-query";
import { lyceums } from "@/lib/lyceums";
import { useAct } from "@/lib/catalog";
import { fmtDate, nm } from "@/lib/util";
import { Btn, StatusBadge } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";

const KEY = [["lyceum-rep-apps"]] as const;

export function RepApplications() {
  const apps = useQuery({ queryKey: KEY[0], queryFn: () => lyceums.applications() });
  const names = useQuery({ queryKey: ["lyceum-list", ""], queryFn: () => lyceums.list("") });
  const label = (id: string) => nm(names.data?.find((l) => l.id === id)?.names, id);
  const approve = useAct((a: { l: string; u: string }) => lyceums.approve(a.l, a.u), KEY, "Representative approved");
  const reject = useAct((a: { l: string; u: string }) => lyceums.reject(a.l, a.u), KEY, "Application rejected");
  const busy = approve.isPending || reject.isPending;
  return (
    <div className="min-h-0 flex-1 overflow-auto">
      <DataTable rows={apps.data} loading={apps.isLoading} error={apps.error} rowKey={(r) => `${r.lyceum_id}:${r.user_id}`} empty="No pending applications."
        cols={[
          { key: "l", head: "Lyceum", cell: (r) => label(r.lyceum_id) },
          { key: "u", head: "User", cell: (r) => <code className="text-xs">{r.user_id}</code> },
          { key: "n", head: "Proof", cell: (r) => <span className="whitespace-pre-wrap">{r.note ?? "—"}</span>, className: "max-w-md" },
          { key: "s", head: "Status", cell: (r) => <StatusBadge status={r.status} /> },
          { key: "d", head: "Applied", cell: (r) => fmtDate(r.created_at) },
          { key: "a", head: "", cell: (r) => (
            <div className="flex gap-1.5">
              <Btn variant="primary" disabled={busy} onClick={() => approve.mutate({ l: r.lyceum_id, u: r.user_id })}>Approve</Btn>
              <Btn variant="danger" disabled={busy} onClick={() => reject.mutate({ l: r.lyceum_id, u: r.user_id })}>Reject</Btn>
            </div>
          ) },
        ]} />
    </div>
  );
}
