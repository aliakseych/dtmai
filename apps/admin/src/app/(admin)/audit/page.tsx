"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { catalog } from "@/lib/catalog";
import { fmtDate } from "@/lib/util";
import { Badge, Field, Input, PageHeader, Toolbar } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";
import { Drawer } from "@/components/ui/overlay";
import type { Audit } from "@/lib/catalog";

export default function AuditPage() {
  const [entity, setEntity] = useState("");
  const [entityId, setEntityId] = useState("");
  const [sel, setSel] = useState<Audit | null>(null);
  const q = useQuery({ queryKey: ["audit", entity, entityId], queryFn: () => catalog.audit({ entity: entity || undefined, entity_id: entityId || undefined, limit: 200 }) });
  return (
    <>
      <PageHeader title="Audit log" sub="Latest 200 catalog changes." />
      <Toolbar>
        <Field label="Entity"><Input value={entity} onChange={(e) => setEntity(e.target.value)} placeholder="subject, path, blueprint…" /></Field>
        <Field label="Entity id"><Input value={entityId} onChange={(e) => setEntityId(e.target.value)} /></Field>
      </Toolbar>
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(r) => String(r.id)} onRow={setSel}
          cols={[
            { key: "id", head: "#", cell: (r) => r.id },
            { key: "a", head: "Actor", cell: (r) => r.actor ?? "system" },
            { key: "ac", head: "Action", cell: (r) => <Badge tone="blue">{r.action}</Badge> },
            { key: "e", head: "Entity", cell: (r) => r.entity },
            { key: "i", head: "Entity id", cell: (r) => <code className="text-xs">{r.entity_id}</code> },
          ]} />
      </div>
      <Drawer open={!!sel} onClose={() => setSel(null)} title={sel ? `${sel.action} ${sel.entity}` : ""}>
        {sel && <div className="grid grid-cols-2 gap-3 text-xs">
          <div><h3 className="mb-1 text-sm">Before</h3><pre className="overflow-auto rounded bg-snow p-2">{JSON.stringify(sel.before, null, 2)}</pre></div>
          <div><h3 className="mb-1 text-sm">After</h3><pre className="overflow-auto rounded bg-snow p-2">{JSON.stringify(sel.after, null, 2)}</pre></div>
        </div>}
      </Drawer>
    </>
  );
}
