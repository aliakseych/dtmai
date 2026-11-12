"use client";
import Link from "next/link";
import { buttonClass, Card } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { api, type Attempt, type AttemptResult } from "@/lib/api";
import { fmt } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";
import { useMemo } from "react";
import { toItems } from "./items";
import { ReviewList } from "./ReviewList";
import { useSubjectNames } from "./useSubjectNames";

async function load(id: string): Promise<{ result: AttemptResult; attempt: Attempt }> {
  const params = { params: { path: { attempt_id: id } } };
  const [result, attempt] = await Promise.all([
    api.unwrap(api.client.GET("/v1/assessment/attempts/{attempt_id}/result", params)),
    api.unwrap(api.client.GET("/v1/assessment/attempts/{attempt_id}", params)),
  ]);
  return { result, attempt };
}

export function MockResult({ attemptId }: { attemptId: string }) {
  const t = useT();
  const { state, reload } = useAsync(() => load(attemptId), [attemptId]);
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-6 pb-[max(2rem,env(safe-area-inset-bottom))]">
      <h1 className="text-3xl text-ink">{t("mock.result")}</h1>
      <AsyncView state={state} onRetry={reload}>
        {({ result, attempt }) => <Body result={result} attempt={attempt} />}
      </AsyncView>
    </div>
  );
}

function Body({ result, attempt }: { result: AttemptResult; attempt: Attempt }) {
  const t = useT();
  const { locale } = useLocale();
  const { name } = useSubjectNames();
  const num = fmt(locale);
  const cmp = result.comparison;
  const items = useMemo(() => toItems(attempt.items), [attempt]);

  const weakest = (() => {
    const counts = new Map<string, number>();
    for (const r of result.review)
      if (!r.correct) {
        const s = items.find((i) => i.id === r.question_id)?.subject_id;
        if (s) counts.set(s, (counts.get(s) ?? 0) + 1);
      }
    return [...counts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0];
  })();
  const practiceHref = weakest ? `/practice/run/?kind=drill&subject=${weakest}` : "/practice/";

  return (
    <>
      {result.submit_reason === "auto" && (
        <p role="status" className="rounded-xl bg-accent px-4 py-2 font-bold">
          {t("mock.autoSubmitted")}
        </p>
      )}
      <Card className="flex flex-col items-center gap-1 text-center">
        <p className="text-sm font-bold uppercase text-ink-soft">{t("mock.total")}</p>
        <p className="text-6xl font-extrabold text-brand">
          {num.format(result.total)}
          <span className="text-2xl text-ink-soft"> / {num.format(result.max_total)}</span>
        </p>
        <p className="text-ink-soft">{t("mock.correctOf", { n: result.correct, total: result.questions })}</p>
      </Card>

      {Object.keys(result.subject_scores).length > 0 && (
        <section aria-labelledby="by-subject" className="flex flex-col gap-3">
          <h2 id="by-subject" className="text-sm uppercase text-ink-soft">
            {t("mock.bySubject")}
          </h2>
          <ul className="flex flex-col gap-2">
            {Object.entries(result.subject_scores).map(([sid, score]) => {
              const weight = attempt.sections.find((s) => s.subject_id === sid)?.weight;
              return (
                <li key={sid}>
                  <Card className="flex items-center justify-between gap-3 py-3">
                    <span className="font-bold">{name(sid)}</span>
                    <span className="flex items-baseline gap-3">
                      {weight !== undefined && <span className="text-sm text-ink-soft">{t("mock.weight", { w: num.format(weight) })}</span>}
                      <span className="text-xl font-extrabold">{num.format(score)}</span>
                    </span>
                  </Card>
                </li>
              );
            })}
          </ul>
        </section>
      )}

      <section aria-labelledby="lyceum" className="flex flex-col gap-2">
        <h2 id="lyceum" className="text-sm uppercase text-ink-soft">
          {t("mock.lyceum")}
          {cmp?.year ? ` · ${cmp.year}` : ""}
        </h2>
        <Card className="flex flex-col gap-1">
          {cmp && (cmp.passing_score !== null || cmp.competition_ratio !== null) ? (
            <>
              {cmp.passing_score !== null && <p className="font-bold">{t("mock.passing", { n: num.format(cmp.passing_score) })}</p>}
              {cmp.competition_ratio !== null && <p className="font-bold">{t("mock.competition", { n: num.format(cmp.competition_ratio) })}</p>}
              {cmp.gap !== null && cmp.on_track !== null && (
                <p className={`font-extrabold ${cmp.on_track ? "text-brand" : "text-red-deep"}`}>
                  {cmp.on_track ? t("mock.onTrack", { n: num.format(Math.abs(cmp.gap)) }) : t("mock.offTrack", { n: num.format(Math.abs(cmp.gap)) })}
                </p>
              )}
            </>
          ) : (
            <p className="font-semibold text-ink-soft">{t("mock.comparisonNone")}</p>
          )}
        </Card>
      </section>

      <section aria-labelledby="review" className="flex flex-col gap-3">
        <h2 id="review" className="text-sm uppercase text-ink-soft">
          {t("mock.review")}
        </h2>
        <ReviewList review={result.review} items={items} flags={attempt.flags} />
      </section>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Link href={practiceHref} className={buttonClass("primary", true)}>
          {t("mock.practiceWeak")}
        </Link>
        <Link href="/mocks/" className={buttonClass("secondary", true)}>
          {t("mock.back")}
        </Link>
      </div>
    </>
  );
}
