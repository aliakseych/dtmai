"use client";
import Link from "next/link";
import { buttonClass, Card } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { api } from "@/lib/api";
import { pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";

type Topic = { id: string; names: Record<string, string>; parent_id: string | null; position: number; active: boolean };

/** Flattens the topic tree depth-first, keeping each topic's depth for indentation. */
function flatten(topics: Topic[]): { topic: Topic; depth: number }[] {
  const ids = new Set(topics.map((x) => x.id));
  const kids = (parent: string | null) => topics.filter((x) => (x.parent_id && ids.has(x.parent_id) ? x.parent_id : null) === parent).sort((a, b) => a.position - b.position);
  const out: { topic: Topic; depth: number }[] = [];
  const walk = (parent: string | null, depth: number) => {
    for (const topic of kids(parent)) {
      out.push({ topic, depth });
      walk(topic.id, depth + 1);
    }
  };
  walk(null, 0);
  return out;
}

/** Per-subject topic list with mastery; every topic starts a drill. */
export function TopicBrowser({ subjectId }: { subjectId: string }) {
  const t = useT();
  const { locale } = useLocale();
  const topics = useAsync(async () => {
    const [list, mastery] = await Promise.all([
      api.unwrap(api.client.GET("/v1/catalog/subjects/{subject_id}/topics", { params: { path: { subject_id: subjectId } } })),
      api.unwrap(api.client.GET("/v1/learning/mastery/{subject_id}", { params: { path: { subject_id: subjectId } } })),
    ]);
    // Attempt-weighted mean of the per-question-type scores of each topic.
    const acc = new Map<string, { sum: number; n: number }>();
    for (const m of mastery) {
      if (!m.topic_id) continue;
      const a = acc.get(m.topic_id) ?? { sum: 0, n: 0 };
      const w = Math.max(1, m.attempts);
      acc.set(m.topic_id, { sum: a.sum + m.score * w, n: a.n + w });
    }
    const score = new Map([...acc].map(([id, a]) => [id, a.sum / a.n]));
    return { rows: flatten((list as Topic[]).filter((x) => x.active)), score };
  }, [subjectId]);

  return (
    <Card className="flex flex-col gap-3">
      <h2 className="text-xl">{t("practice.topics")}</h2>
      <AsyncView state={topics.state} onRetry={topics.reload} isEmpty={(d) => d.rows.length === 0} emptyText={t("practice.topics.empty")}>
        {({ rows, score }) => (
          <ul className="flex flex-col gap-2">
            {rows.map(({ topic, depth }) => {
              const s = score.get(topic.id);
              const pct = s === undefined ? null : Math.round(s * 100);
              return (
                <li key={topic.id} style={{ marginInlineStart: depth * 16 }} className="flex items-center gap-3 rounded-2xl border-2 border-line px-3 py-2">
                  <div className="min-w-0 flex-1">
                    <p className="break-words font-bold text-ink">{pick(topic.names, locale)}</p>
                    <div className="mt-1 h-2 overflow-hidden rounded-full bg-line" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct ?? 0}>
                      <div className="h-full rounded-full bg-brand" style={{ width: `${pct ?? 0}%` }} />
                    </div>
                    <p className="mt-1 text-xs text-ink-soft">{pct === null ? t("practice.topic.new") : t("practice.topic.mastery", { n: pct })}</p>
                  </div>
                  <Link href={`/practice/run/?kind=drill&subject=${subjectId}&topic=${topic.id}`} className={buttonClass("secondary", false, "min-h-11 shrink-0 px-3 py-1.5 text-xs")}>
                    {t("practice.drill")}
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </AsyncView>
    </Card>
  );
}
