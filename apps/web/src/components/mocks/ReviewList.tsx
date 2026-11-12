"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ApiError } from "@dtmai/api-client";
import { Card } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { RichText } from "@/components/RichText";
import { Markdown } from "@/components/temur/Markdown";
import { correctText, QuestionBody } from "@/components/lesson/QuestionBody";
import { api, type AttemptResult, type ItemOut } from "@/lib/api";
import { useBilling } from "@/lib/billing";

type Explain = { text?: string; limit?: boolean; guest?: boolean; failed?: boolean; busy?: boolean };
/** Client-side cap on one AI explanation; the server aborts its model call a little earlier. */
const EXPLAIN_TIMEOUT_MS = 45_000;

type Filter = "all" | "wrong" | "flagged";
const noop = () => {};

/** Every answered question with a filter (all / wrong / flagged); wrong ones offer an on-demand AI explanation. */
export function ReviewList({ review, items, flags }: { review: AttemptResult["review"]; items: ItemOut[]; flags: string[] }) {
  const t = useT();
  const { canBuy } = useBilling();
  const [explain, setExplain] = useState<Record<string, Explain>>({});
  const [filter, setFilter] = useState<Filter>("all");
  const explainCancelled = useRef(new Set<string>());
  const aborts = useRef<Record<string, AbortController>>({});
  useEffect(() => {
    const live = aborts.current;
    return () => Object.values(live).forEach((c) => c.abort());
  }, []);
  const shown = review.filter((r) => (filter === "wrong" ? !r.correct : filter === "flagged" ? flags.includes(r.question_id) : true));

  async function ask(id: string) {
    setExplain((e) => ({ ...e, [id]: { busy: true } }));
    const ctl = new AbortController();
    aborts.current[id] = ctl;
    const timer = setTimeout(() => ctl.abort(), EXPLAIN_TIMEOUT_MS);
    try {
      const r = await api.unwrap(api.client.POST("/v1/ai/explain/{question_id}", { params: { path: { question_id: id } }, signal: ctl.signal }));
      setExplain((e) => ({ ...e, [id]: { text: r.explanation } }));
    } catch (e) {
      if (ctl.signal.aborted && !(e instanceof ApiError) && explainCancelled.current.has(id)) {
        explainCancelled.current.delete(id);
        setExplain((x) => ({ ...x, [id]: {} }));
        return;
      }
      setExplain((x) => ({
        ...x,
        [id]:
          e instanceof ApiError && e.status === 403
            ? { guest: true }
            : e instanceof ApiError && [402, 429].includes(e.status)
              ? { limit: true }
              : { failed: true },
      }));
    } finally {
      clearTimeout(timer);
      delete aborts.current[id];
    }
  }

  function cancel(id: string) {
    explainCancelled.current.add(id);
    aborts.current[id]?.abort();
  }

  if (review.length === 0) return <p className="font-bold text-brand">{t("mock.reviewNone")}</p>;
  const filters: { id: Filter; label: string }[] = [
    { id: "all", label: t("mock.filterAll") },
    { id: "wrong", label: t("mock.filterWrong") },
    { id: "flagged", label: t("mock.filterFlagged") },
  ];
  return (
    <>
      <div role="group" aria-label={t("mock.review")} className="flex flex-wrap gap-2">
        {filters.map((f) => (
          <button
            key={f.id}
            type="button"
            aria-pressed={filter === f.id}
            onClick={() => setFilter(f.id)}
            className={`rounded-xl border-2 px-3 py-1.5 font-bold ${filter === f.id ? "border-brand bg-brand text-white" : "border-line text-ink-soft"}`}
          >
            {f.label}
          </button>
        ))}
      </div>
      {shown.length === 0 && <p className="font-bold text-ink-soft">{t("mock.reviewEmpty")}</p>}
    <ol className="flex flex-col gap-4">
      {shown.map((r) => {
        const item = items.find((i) => i.id === r.question_id);
        if (!item) return null;
        const ex = explain[r.question_id];
        const isGroup = item.kind === "passage_group";
        const mine = r.answered ? correctText(item, r.response) : "";
        return (
          <li key={r.question_id}>
            <Card className="flex flex-col gap-3">
              {isGroup ? (
                <QuestionBody item={item} value={r.response} onChange={noop} disabled correct={r.correct_response} wasCorrect={r.correct} />
              ) : (
                <>
                  <h3 className="text-lg">
                    <RichText text={item.stem} />
                  </h3>
                  {r.correct ? (
                    <p className="rounded-xl bg-brand-soft px-3 py-2 font-semibold text-brand">
                      <span className="block text-xs font-bold uppercase">{t("mock.correctBadge")}</span>
                      <RichText text={correctText(item, r.correct_response)} />
                    </p>
                  ) : (
                    <>
                      <p className="rounded-xl bg-red-soft px-3 py-2 font-semibold text-red-deep">
                        <span className="block text-xs font-bold uppercase">{t("mock.yourAnswer")}</span>
                        {mine ? <RichText text={mine} /> : t("mock.noAnswer")}
                      </p>
                      <p className="rounded-xl bg-brand-soft px-3 py-2 font-semibold text-brand">
                        <span className="block text-xs font-bold uppercase">{t("mock.correctAnswer")}</span>
                        <RichText text={correctText(item, r.correct_response)} />
                      </p>
                    </>
                  )}
                </>
              )}
              {isGroup ? null : ex?.text ? (
                <div className="font-semibold">
                  <Markdown text={ex.text} />
                </div>
              ) : ex?.guest ? (
                <p className="font-semibold">
                  {t("lesson.explainGuest")}{" "}
                  <Link href="/register/" className="underline">{t("lesson.explainSignUp")}</Link>
                </p>
              ) : ex?.limit ? (
                <p className="font-semibold">
                  {t("lesson.explainLimit")}{" "}
                  {canBuy && (
                    <Link href="/premium/" className="underline">
                      {t("mock.premiumGo")}
                    </Link>
                  )}
                </p>
              ) : ex?.busy ? (
                <div role="status" className="flex flex-wrap items-center gap-x-4 font-semibold text-ink-soft">
                  <span className="animate-pulse motion-reduce:animate-none">
                    {t("lesson.explaining")} {t("mock.explainWait")}
                  </span>
                  <button type="button" onClick={() => cancel(r.question_id)} className="inline-flex min-h-11 items-center font-extrabold text-brand underline">
                    {t("mock.explainCancel")}
                  </button>
                </div>
              ) : (
                <>
                  {ex?.failed && (
                    <p role="alert" className="font-semibold text-red-deep">
                      {t("mock.explainFailed")}
                    </p>
                  )}
                  <button type="button" onClick={() => void ask(r.question_id)} className="inline-flex min-h-11 items-center self-start font-extrabold text-brand underline">
                    {ex?.failed ? t("common.retry") : t("lesson.explain")}
                  </button>
                </>
              )}
            </Card>
          </li>
        );
      })}
    </ol>
    </>
  );
}
