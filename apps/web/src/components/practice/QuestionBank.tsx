"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { buttonClass, Card, ProgressBar, Tabs } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { PageTitle } from "@/components/PageTitle";
import { api } from "@/lib/api";
import { useLearnLanguage } from "@/lib/auth";
import { pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";

type Level = "all" | "easy" | "medium" | "hard";
const LEVELS: Level[] = ["all", "easy", "medium", "hard"];

/** Learner question bank of one subject: topics -> question types with solved state, filtered by question base and difficulty. */
export function QuestionBank() {
  const t = useT();
  const { locale } = useLocale();
  const language = useLearnLanguage();
  const subject = useSearchParams().get("subject") ?? "";
  const [level, setLevel] = useState<Level>("all");
  const [base, setBase] = useState("all");
  const [unsolved, setUnsolved] = useState(false);

  const data = useAsync(async () => {
    const [topics, overview] = await Promise.all([
      api.unwrap(api.client.GET("/v1/catalog/subjects/{subject_id}/topics", { params: { path: { subject_id: subject } } })),
      api.unwrap(
        api.client.GET("/v1/bank/overview", {
          params: { query: { subject_id: subject, language, level: level === "all" ? undefined : level, source_id: base === "all" ? undefined : base } },
        }),
      ),
    ]);
    return { topics, overview };
  }, [subject, language, level, base]);

  const run = (extra: string) => `/practice/run/?kind=drill&subject=${subject}${extra}${base === "all" ? "" : `&source=${base}`}${level === "all" ? "" : `&level=${level}`}${unsolved ? "&unsolved=1" : ""}`;

  return (
    <>
      <PageTitle>{t("bank.title")}</PageTitle>
      <AsyncView state={data.state} onRetry={data.reload} exitHref="/practice/" isEmpty={(d) => d.overview.total === 0 && d.overview.bases.length === 0} emptyText={t("bank.empty")}>
        {({ topics, overview }) => {
          const names = new Map(topics.map((x) => [x.id, pick(x.names, locale)]));
          const order = new Map(topics.map((x, i) => [x.id, x.position * 1000 + i]));
          const groups = new Map<string, typeof overview.types>();
          for (const c of overview.types) groups.set(c.topic_id, [...(groups.get(c.topic_id) ?? []), c]);
          const rows = [...groups].sort((a, b) => (order.get(a[0]) ?? 0) - (order.get(b[0]) ?? 0));
          return (
            <div className="flex flex-col gap-4">
              <Card className="flex flex-col gap-3">
                <div className="flex items-baseline justify-between gap-3">
                  <h2 className="text-xl">{t("bank.progress")}</h2>
                  <span className="font-bold text-ink-soft">{t("bank.solvedOf", { solved: overview.solved, total: overview.total })}</span>
                </div>
                <ProgressBar value={overview.solved} max={Math.max(1, overview.total)} label={t("bank.progress")} />
                <Tabs className="flex-wrap" items={LEVELS.map((l) => ({ id: l, label: t(`bank.level.${l}`) }))} value={level} onChange={setLevel} />
                {overview.bases.length > 0 && (
                  <Tabs
                    className="flex-wrap"
                    items={[{ id: "all", label: t("bank.base.all") }, ...overview.bases.map((b) => ({ id: b.id, label: `${pick(b.names, locale)}${b.year ? ` ${b.year}` : ""} · ${b.total}` }))]}
                    value={base}
                    onChange={setBase}
                  />
                )}
                <label className="flex min-h-11 items-center gap-3 font-bold text-ink">
                  <input type="checkbox" className="h-5 w-5 accent-brand" checked={unsolved} onChange={(e) => setUnsolved(e.target.checked)} />
                  {t("bank.unsolvedOnly")}
                </label>
                {overview.total === 0 || rows.length === 0 ? (
                  <span aria-disabled="true" className={buttonClass("primary", true, "pointer-events-none opacity-50")}>
                    {t("bank.practiceAll")}
                  </span>
                ) : (
                  <Link href={run("")} className={buttonClass("primary", true)}>
                    {t("bank.practiceAll")}
                  </Link>
                )}
              </Card>
              {rows.length === 0 && <p className="text-center text-ink-soft">{t("bank.noMatch")}</p>}
              {rows.map(([topicId, cells]) => (
                <Card key={topicId} className="flex flex-col gap-2">
                  <h2 className="break-words text-lg">{names.get(topicId) ?? t("practice.weak.generic")}</h2>
                  <ul className="flex flex-col gap-2">
                    {cells.map((c) => {
                      const done = c.solved >= c.total;
                      return (
                        <li key={c.type_id} className="flex items-center gap-3 rounded-2xl border-2 border-line px-3 py-2">
                          <div className="min-w-0 flex-1">
                            <p className="break-words font-bold text-ink">{pick(c.type_names, locale)}</p>
                            <ProgressBar value={c.solved} max={c.total} label={pick(c.type_names, locale)} className="mt-1" />
                            <p className="mt-1 text-xs text-ink-soft">
                              {t("bank.solvedOf", { solved: c.solved, total: c.total })} · {t("bank.level.easy")} {c.easy} · {t("bank.level.medium")} {c.medium} · {t("bank.level.hard")} {c.hard}
                            </p>
                          </div>
                          <Link
                            href={run(`&topic=${topicId}&type=${c.type_id}`)}
                            className={buttonClass("secondary", false, "min-h-11 shrink-0 px-3 py-1.5 text-xs")}
                          >
                            {done ? t("bank.again") : t("practice.drill")}
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                </Card>
              ))}
            </div>
          );
        }}
      </AsyncView>
    </>
  );
}
