"use client";
import { useT } from "@/lib/i18n";
import { useState } from "react";
import { useAct } from "@/lib/catalog";
import { labeling, type LFilters } from "@/lib/labeling";
import { Btn, Field, Input } from "@/components/ui/controls";
import { Dialog } from "@/components/ui/overlay";
import { useConfirm } from "@/components/ui/confirm";

export function BulkDialog({ filters, onClose }: { filters: LFilters; onClose: () => void }) {
  const t = useT();
  const [minConf, setMinConf] = useState(0.9);
  const [limit, setLimit] = useState(200);
  const [size, setSize] = useState(50);
  const run = useAct((dry_run: boolean) => labeling.bulkApprove({ ...filters, min_confidence: minConf, limit, dry_run }), [["labeling-stats"]]);
  const sample = useAct(() => labeling.sampleAudit({ ...filters, size }), [["labeling-stats"]]);
  const [ask, confirmNode] = useConfirm();
  return (
    <Dialog open onClose={onClose} title={t("admin.labeling.bulkApproveAuditSampling")} footer={<Btn onClick={onClose}>{t("admin.common.close")}</Btn>}>
      <div className="space-y-4">
        <section className="space-y-2">
          <h3 className="text-sm">{t("admin.labeling.approveAutoAgreedQuestions")}</h3>
          <p className="text-xs text-ink-soft">{t("admin.labeling.usesTheCurrentQueue")}</p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Field label={t("admin.labeling.minConfidence", { pct: (minConf * 100).toFixed(0) })}><input type="range" min={0.5} max={1} step={0.01} value={minConf} onChange={(e) => setMinConf(Number(e.target.value))} className="w-full accent-blue" /></Field>
            <Field label={t("admin.labeling.maxQuestions")}><Input type="number" min={1} max={2000} value={limit} onChange={(e) => setLimit(Number(e.target.value))} /></Field>
          </div>
          <div className="flex gap-2"><Btn disabled={run.isPending} onClick={() => run.mutate(true)}>{t("admin.labeling.dryRun")}</Btn><Btn variant="primary" disabled={run.isPending} onClick={() => ask({ title: t("admin.labeling.approveTitle"), body: t("admin.labeling.confirmApprove", { limit, pct: (minConf * 100).toFixed(0) }), confirmLabel: t("admin.common.approve") }, () => run.mutate(false))}>{t("admin.common.approve")}</Btn></div>
          {run.data && <p className="text-sm" role="status">{t(run.variables ? "admin.labeling.dryRunResult" : "admin.labeling.approveResult", { approved: run.data.approved, failed: run.data.failed, rate: run.data.audit.rate == null ? t("admin.common.na") : `${(run.data.audit.rate * 100).toFixed(1)}% (${run.data.audit.matched}/${run.data.audit.audited})` })}</p>}
        </section>
        <section className="space-y-2 border-t border-line pt-3">
          <h3 className="text-sm">{t("admin.labeling.sampleABlindAudit")}</h3>
          <div className="flex flex-wrap items-end gap-2"><Field label={t("admin.labeling.size")}><Input type="number" min={1} value={size} onChange={(e) => setSize(Number(e.target.value))} /></Field><Btn disabled={sample.isPending} onClick={() => sample.mutate()}>{t("admin.labeling.sample")}</Btn></div>
          {sample.data && <p className="text-sm">{t("admin.labeling.sampledResult", { n: sample.data.sampled, batch: sample.data.batch_id.slice(0, 8) })}</p>}
        </section>
      </div>
      {confirmNode}
    </Dialog>
  );
}
