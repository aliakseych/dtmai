"use client";
import Link from "next/link";
import { useState } from "react";
import { buttonClass, Card, Tabs } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { PageTitle } from "@/components/PageTitle";
import { api } from "@/lib/api";
import { useBilling } from "@/lib/billing";
import { pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";
import { TopicBrowser } from "@/components/practice/TopicBrowser";

function Panel({ subjectId }: { subjectId: string }) {
  const t = useT();
  const { canBuy } = useBilling();
  const review = useAsync(() => api.unwrap(api.client.GET("/v1/learning/review/summary", { params: { query: { subject_id: subjectId } } })), [subjectId]);
  const weak = useAsync(() => api.unwrap(api.client.GET("/v1/learning/weak-areas/{subject_id}", { params: { path: { subject_id: subjectId } } })), [subjectId]);
  const run = (kind: string) => `/practice/run/?kind=${kind}&subject=${subjectId}`;
  return (
    <div className="flex flex-col gap-4">
      <AsyncView state={review.state} onRetry={review.reload}>
        {(r) => (
          <Card className="flex flex-col gap-3">
            <h2 className="text-xl">{t("practice.mistakes")}</h2>
            <p className="text-ink-soft">{r.due > 0 ? t("practice.mistakes.due", { n: r.due }) : t("practice.mistakes.none")}</p>
            {r.due > 0 ? (
              <Link href={run("review")} className={buttonClass("primary", true)}>
                {t("common.start")}
              </Link>
            ) : (
              <Link href={run("drill")} className={buttonClass("secondary", true)}>
                {t("practice.bank")}
              </Link>
            )}
          </Card>
        )}
      </AsyncView>
      <Card className="flex flex-col gap-3">
        <h2 className="text-xl">{t("rush.title")}</h2>
        <p className="text-ink-soft">{t("rush.text")}</p>
        <Link href={`/practice/rush/?subject=${subjectId}`} className={buttonClass("super", true)}>
          {t("rush.play")}
        </Link>
      </Card>
      <TopicBrowser subjectId={subjectId} />
      <Card className="flex flex-col gap-3">
        <h2 className="text-xl">{t("practice.weak")}</h2>
        <p className="text-ink-soft">{t("practice.weak.text")}</p>
        <AsyncView state={weak.state} onRetry={weak.reload} isEmpty={(d) => d.length === 0} emptyText={t("practice.weak.empty")}>
          {(areas) => (
            <ul className="flex flex-col gap-2">
              {areas.map((a) => (
                <li key={`${a.type_id}-${a.topic_id}`} className="flex items-center justify-between gap-3 rounded-2xl border-2 border-line px-3 py-2">
                  <span className="font-bold text-ink">{a.topic_name || t("practice.weak.generic")}</span>
                  <span className="text-ink-soft">{Math.round(a.score * 100)}%</span>
                  <Link
                    href={`${run("drill")}${a.topic_id ? `&topic=${a.topic_id}` : ""}&type=${a.type_id}`}
                    className={buttonClass("secondary", false, "px-3 py-1.5 text-xs")}
                  >
                    {t("practice.drill")}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </AsyncView>
      </Card>
      <Card className="flex flex-col gap-3">
        <h2 className="text-xl">{t("practice.personalMock")}</h2>
        <p className="text-ink-soft">{t("practice.personalMock.text")}</p>
        {canBuy ? (
          <Link href="/premium/" className={buttonClass("super", true)}>
            {t("practice.premiumOnly")}
          </Link>
        ) : (
          <span className="font-bold text-ink-soft">{t("common.soon")}</span>
        )}
      </Card>
    </div>
  );
}

export function PracticeView() {
  const t = useT();
  const { locale } = useLocale();
  const subjects = useAsync(() => api.unwrap(api.client.GET("/v1/catalog/subjects")), []);
  const [active, setActive] = useState<string | null>(null);
  return (
    <>
      <PageTitle>{t("practice.title")}</PageTitle>
      <AsyncView state={subjects.state} onRetry={subjects.reload} isEmpty={(d) => d.length === 0}>
        {(list) => {
          const current = active ?? list[0].id;
          return (
            <div className="flex flex-col gap-6">
              <Tabs items={list.map((s) => ({ id: s.id, label: pick(s.names, locale) }))} value={current} onChange={setActive} />
              <Panel subjectId={current} />
            </div>
          );
        }}
      </AsyncView>
    </>
  );
}
