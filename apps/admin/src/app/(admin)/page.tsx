"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import { ai } from "@/lib/ai";
import { generation } from "@/lib/generation";
import { ingestion } from "@/lib/ingestion";
import { labeling } from "@/lib/labeling";
import { useEnum, useT } from "@/lib/i18n";
import { Badge, PageHeader } from "@/components/ui/controls";

function Card({ title, value, sub, href, tone }: { title: string; value: React.ReactNode; sub?: React.ReactNode; href: string; tone?: "red" }) {
  return (
    <Link href={href} className="block rounded-card border-2 border-line bg-white p-4 hover:border-blue focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue">
      <p className="text-xs font-bold uppercase text-ink-soft">{title}</p>
      <p className={`mt-1 text-3xl font-black ${tone === "red" ? "text-red-deep" : ""}`}>{value}</p>
      {sub && <p className="mt-1 text-sm text-ink-soft">{sub}</p>}
    </Link>
  );
}

const RUNNING: Record<string, true> = { running: true, pending: true, queued: true, in_progress: true };

export default function Dashboard() {
  const t = useT();
  const en = useEnum();
  const stats = useQuery({ queryKey: ["dash-stats"], queryFn: () => labeling.stats(7) });
  const cov = useQuery({ queryKey: ["dash-cov"], queryFn: () => api.unwrap(api.client.GET("/v1/admin/bank/coverage", { params: { query: {} } })) });
  const spend = useQuery({ queryKey: ["dash-spend"], queryFn: () => ai.spend(1) });
  const gens = useQuery({ queryKey: ["dash-gen"], queryFn: () => generation.list(50), refetchInterval: 15_000 });
  const batches = useQuery({ queryKey: ["dash-batches"], queryFn: () => ingestion.list(50), refetchInterval: 15_000 });

  const depth = Object.entries(stats.data?.queue_depth ?? {});
  const queue = depth.reduce((a, [, n]) => a + n, 0);
  const nh = (stats.data?.queue_depth as Record<string, number> | undefined)?.needs_human ?? 0;
  const verified = (cov.data ?? []).reduce((a, r) => a + r.verified, 0);
  const below = (cov.data ?? []).filter((r) => !r.ok).length;
  const running = (gens.data ?? []).filter((g) => RUNNING[g.status]).length + (batches.data ?? []).filter((b) => RUNNING[b.status]).length;
  const failed = (gens.data ?? []).filter((g) => g.status === "failed").length + (batches.data ?? []).filter((b) => b.status === "failed").length;
  const usd = (n: number) => `$${n.toFixed(2)}`;
  const dash = "—";

  return (
    <>
      <PageHeader title={t("admin.dashboard.title")} sub={t("admin.dashboard.sub")} />
      <div className="min-h-0 flex-1 overflow-auto p-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <Card href="/labeling/" title={t("admin.dashboard.queue")} value={stats.data ? queue : dash} sub={depth.length ? <span className="flex flex-wrap gap-1">{depth.map(([k, n]) => <Badge key={k} tone="gray">{en("state", k)} {n}</Badge>)}</span> : undefined} />
          <Card href="/labeling/" title={t("admin.dashboard.needsHuman")} value={stats.data ? nh : dash} tone={nh ? "red" : undefined} />
          <Card href="/coverage/" title={t("admin.dashboard.verifiedPool")} value={cov.data ? verified.toLocaleString() : dash} sub={cov.data ? t("admin.coverage.belowMin", { n: below }) : undefined} tone={below ? "red" : undefined} />
          <Card href="/ai/" title={t("admin.dashboard.aiSpend")} value={spend.data ? usd(spend.data.spent_today_usd) : dash} sub={spend.data ? t("admin.ai.ofCap", { cap: usd(spend.data.daily_spend_cap_usd) }) : undefined} tone={spend.data && spend.data.daily_spend_cap_usd > 0 && spend.data.spent_today_usd >= spend.data.daily_spend_cap_usd ? "red" : undefined} />
          <Card href="/generation/" title={t("admin.dashboard.runningJobs")} value={gens.data && batches.data ? running : dash} sub={t("admin.dashboard.failedJobs", { n: failed })} tone={failed ? "red" : undefined} />
        </div>
        {(stats.error || cov.error || spend.error || gens.error || batches.error) && <p role="alert" className="mt-4 text-sm font-bold text-red-deep">{t("admin.dashboard.partial")}</p>}
      </div>
    </>
  );
}
