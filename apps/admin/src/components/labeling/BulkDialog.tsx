"use client";
import { useState } from "react";
import { useAct } from "@/lib/catalog";
import { labeling, type LFilters } from "@/lib/labeling";
import { Btn, Field, Input } from "@/components/ui/controls";
import { Dialog } from "@/components/ui/overlay";

export function BulkDialog({ filters, onClose }: { filters: LFilters; onClose: () => void }) {
  const [minConf, setMinConf] = useState(0.9);
  const [limit, setLimit] = useState(200);
  const [size, setSize] = useState(50);
  const run = useAct((dry_run: boolean) => labeling.bulkApprove({ ...filters, min_confidence: minConf, limit, dry_run }), [["labeling-stats"]]);
  const sample = useAct(() => labeling.sampleAudit({ ...filters, size }), [["labeling-stats"]]);
  return (
    <Dialog open onClose={onClose} title="Bulk approve & audit sampling" footer={<Btn onClick={onClose}>Close</Btn>}>
      <div className="space-y-4">
        <section className="space-y-2">
          <h3 className="text-sm">Approve auto-agreed questions above a confidence threshold</h3>
          <p className="text-xs text-ink-soft">Uses the current queue filters. The server refuses when blind-audit agreement is below its minimum.</p>
          <div className="grid grid-cols-2 gap-3">
            <Field label={`Min confidence: ${(minConf * 100).toFixed(0)}%`}><input type="range" min={0.5} max={1} step={0.01} value={minConf} onChange={(e) => setMinConf(Number(e.target.value))} className="w-full accent-blue" /></Field>
            <Field label="Max questions"><Input type="number" min={1} max={2000} value={limit} onChange={(e) => setLimit(Number(e.target.value))} /></Field>
          </div>
          <div className="flex gap-2"><Btn disabled={run.isPending} onClick={() => run.mutate(true)}>Dry run</Btn><Btn variant="primary" disabled={run.isPending} onClick={() => confirm(`Approve up to ${limit} questions at ≥ ${(minConf * 100).toFixed(0)}% confidence?`) && run.mutate(false)}>Approve</Btn></div>
          {run.data && <p className="text-sm"><b>{run.data.approved}</b> approved, {run.data.failed} failed · audit agreement {run.data.audit.rate == null ? "n/a" : `${(run.data.audit.rate * 100).toFixed(1)}% (${run.data.audit.matched}/${run.data.audit.audited})`}</p>}
        </section>
        <section className="space-y-2 border-t border-line pt-3">
          <h3 className="text-sm">Sample a blind audit batch</h3>
          <div className="flex items-end gap-2"><Field label="Size"><Input type="number" min={1} value={size} onChange={(e) => setSize(Number(e.target.value))} /></Field><Btn disabled={sample.isPending} onClick={() => sample.mutate()}>Sample</Btn></div>
          {sample.data && <p className="text-sm">{sample.data.sampled} questions sampled (batch <code>{sample.data.batch_id.slice(0, 8)}</code>).</p>}
        </section>
      </div>
    </Dialog>
  );
}
