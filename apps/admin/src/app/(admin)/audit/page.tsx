"use client";
import { useT } from "@/lib/i18n";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { catalog } from "@/lib/catalog";
import { fmtDate } from "@/lib/util";
import { Badge, Field, Input, PageHeader, Toolbar } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";
import { Drawer } from "@/components/ui/overlay";
import type { Audit } from "@/lib/catalog";

export default function AuditPage() {
  const t = useT();
  const [entity, setEntity] = useState("");
  const [entityId, setEntityId] = useState("");
  const [sel, setSel] = useState<Audit | null>(null);
  const q = useQuery({ queryKey: ["audit", entity, entityId], queryFn: () => catalog.audit({ entity: entity || undefined, entity_id: entityId || undefined, limit: 200 }) });
  return (
    <>
      <PageHeader title={t("admin.audit.auditLog")} sub={t("admin.audit.latest200CatalogChanges")} />
      <Toolbar>
        <Field label={t("admin.audit.entity")}><Input value={entity} onChange={(e) => setEntity(e.target.value)} placeholder={t("admin.audit.subjectPathBlueprint")} /></Field>
        <Field label={t("admin.audit.entityId")}><Input value={entityId} onChange={(e) => setEntityId(e.target.value)} /></Field>
      </Toolbar>
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={q.data} loading={q.isLoading} error={q.error} rowKey={(r) => String(r.id)} onRow={setSel}
          cols={[
            { key: "id", head: "#", cell: (r) => r.id },
            { key: "a", head: t("admin.audit.actor"), cell: (r) => r.actor ?? "system" },
            { key: "ac", head: t("admin.common.action"), cell: (r) => <Badge tone="blue">{r.action}</Badge> },
            { key: "e", head: t("admin.audit.entity"), cell: (r) => r.entity },
            { key: "i", head: t("admin.audit.entityId"), cell: (r) => <code className="text-xs">{r.entity_id}</code> },
          ]} />
      </div>
      <Drawer open={!!sel} onClose={() => setSel(null)} title={sel ? `${sel.action} ${sel.entity}` : ""}>
        {sel && <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div><h3 className="mb-1 text-sm">{t("admin.audit.before")}</h3><pre className="overflow-auto rounded bg-snow p-2">{JSON.stringify(sel.before, null, 2)}</pre></div>
          <div><h3 className="mb-1 text-sm">{t("admin.audit.after")}</h3><pre className="overflow-auto rounded bg-snow p-2">{JSON.stringify(sel.after, null, 2)}</pre></div>
        </div>}
      </Drawer>
    </>
  );
}
