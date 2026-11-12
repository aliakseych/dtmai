"use client";
import { useT } from "@/lib/i18n";
import { useQuery, useQueries } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { api } from "@/lib/api";
import { catalog, qk, useSubjects, useTypes } from "@/lib/catalog";
import { nm } from "@/lib/util";
import { Badge, Field, PageHeader, Select, Toolbar } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";
import { LangInput } from "@/components/ui/lang";
import Link from "next/link";
import { EmptyState } from "@dtmai/ui";

export default function CoveragePage() {
  const t = useT();
  const subjects = useSubjects();
  const types = useTypes();
  const [subjectId, setSubjectId] = useState("");
  const [language, setLanguage] = useState("");
  const [onlyBad, setOnlyBad] = useState(true);
  const cov = useQuery({
    queryKey: ["coverage", subjectId, language],
    queryFn: () => api.unwrap(api.client.GET("/v1/admin/bank/coverage", { params: { query: { subject_id: subjectId || undefined, language: language || undefined } } })),
  });
  const subjectIds = useMemo(() => [...new Set(cov.data?.map((r) => r.subject_id))], [cov.data]);
  const topicQs = useQueries({ queries: subjectIds.map((id) => ({ queryKey: qk.topics(id), queryFn: () => catalog.topics.list(id), staleTime: 60_000 })) });
  const topicName = new Map(topicQs.flatMap((q) => q.data ?? []).map((t) => [t.id, nm(t.names)]));
  const subjName = new Map(subjects.data?.map((s) => [s.id, nm(s.names)]));
  const typeName = new Map(types.data?.map((t) => [t.id, nm(t.names)]));
  const rows = (cov.data ?? []).filter((r) => !onlyBad || !r.ok);
  const bad = (cov.data ?? []).filter((r) => !r.ok).length;

  return (
    <>
      <PageHeader title={t("admin.coverage.coverage")} sub={t("admin.coverage.verifiedQuestionsVsThe")} actions={<Badge tone={bad ? "red" : "green"}>{t("admin.coverage.belowMin", { n: bad })}</Badge>} />
      <Toolbar>
        <Field label={t("admin.common.subject")}><Select value={subjectId} onChange={(e) => setSubjectId(e.target.value)}><option value="">{t("admin.common.all")}</option>{subjects.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select></Field>
        <Field label={t("admin.common.language")}><LangInput value={language} onChange={setLanguage} /></Field>
        <label className="flex min-h-11 items-center gap-1.5 text-sm"><input type="checkbox" className="accent-blue" checked={onlyBad} onChange={(e) => setOnlyBad(e.target.checked)} />{t("admin.coverage.onlyBelowMinimum")}</label>
      </Toolbar>
      <div className="min-h-0 flex-1 overflow-auto">
        {cov.data && cov.data.length === 0 ? <EmptyState compact title={t("admin.coverage.noData")} body={t("admin.coverage.noDataBody")} action={<Link className="font-bold text-blue-deep hover:underline" href="/paths/">{t("admin.nav.paths")}</Link>} /> : <DataTable rows={rows} loading={cov.isLoading} error={cov.error} rowKey={(r) => `${r.topic_id}|${r.type_id}|${r.language}`} empty={t("admin.coverage.everyCellMeetsIts")}
          rowClass={(r) => (r.ok ? undefined : "bg-red-soft/60")}
          cols={[
            { key: "s", head: t("admin.common.subject"), cell: (r) => subjName.get(r.subject_id) ?? r.subject_id },
            { key: "t", head: t("admin.common.topic"), cell: (r) => topicName.get(r.topic_id) ?? r.topic_id },
            { key: "y", head: t("admin.common.type"), cell: (r) => typeName.get(r.type_id) ?? r.type_id },
            { key: "l", head: t("admin.common.lang"), cell: (r) => r.language },
            { key: "v", head: t("admin.common.verified"), cell: (r) => <b className={r.ok ? "" : "text-red-deep"}>{r.verified}</b> },
            { key: "m", head: t("admin.common.min"), cell: (r) => r.min_pool },
            { key: "a", head: "", cell: (r) => <Link className="text-blue-deep hover:underline" href={`/questions/?subject_id=${r.subject_id}&topic_id=${r.topic_id}&type_id=${r.type_id}&language=${r.language}`}>{t("admin.coverage.questions")}</Link> },
          ]} />}
      </div>
    </>
  );
}
