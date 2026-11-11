"use client";
import { useState } from "react";
import Link from "next/link";
import { ApiError } from "@dtmai/api-client";
import { Card } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { RichText } from "@/components/RichText";
import { correctText, QuestionBody } from "@/components/lesson/QuestionBody";
import { api, type AttemptResult, type ItemOut } from "@/lib/api";
import { useBilling } from "@/lib/billing";

type Explain = { text?: string; limit?: boolean; failed?: boolean; busy?: boolean };

type Filter = "all" | "wrong" | "flagged";
const noop = () => {};

/** Every answered question with a filter (all / wrong / flagged); wrong ones offer an on-demand AI explanation. */
export function ReviewList({ review, items, flags }: { review: AttemptResult["review"]; items: ItemOut[]; flags: string[] }) {
  const t = useT();
  const { canBuy } = useBilling();
  const [explain, setExplain] = useState<Record<string, Explain>>({});
  const [filter, setFilter] = useState<Filter>("all");
  const shown = review.filter((r) => (filter === "wrong" ? !r.correct : filter === "flagged" ? flags.includes(r.question_id) : true));

  async function ask(id: string) {
    setExplain((e) => ({ ...e, [id]: { busy: true } }));
    try {
      const r = await api.unwrap(api.client.POST("/v1/ai/explain/{question_id}", { params: { path: { question_id: id } } }));
      setExplain((e) => ({ ...e, [id]: { text: r.explanation } }));
    } catch (e) {
      setExplain((x) => ({ ...x, [id]: e instanceof ApiError && [402, 403, 429].includes(e.status) ? { limit: true } : { failed: true } }));
    }
  }

  if (review.length === 0) return <p className="font-bold text-green-deep">{t("mock.reviewNone")}</p>;
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
            className={`rounded-xl border-2 px-3 py-1.5 font-bold ${filter === f.id ? "border-blue bg-blue text-white" : "border-line text-ink-soft"}`}
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
                    <p className="rounded-xl bg-green-soft px-3 py-2 font-semibold text-green-deep">
                      <span className="block text-xs font-bold uppercase">{t("mock.correctBadge")}</span>
                      {correctText(item, r.correct_response)}
                    </p>
                  ) : (
                    <>
                      <p className="rounded-xl bg-red-soft px-3 py-2 font-semibold text-red-deep">
                        <span className="block text-xs font-bold uppercase">{t("mock.yourAnswer")}</span>
                        {mine || t("mock.noAnswer")}
                      </p>
                      <p className="rounded-xl bg-green-soft px-3 py-2 font-semibold text-green-deep">
                        <span className="block text-xs font-bold uppercase">{t("mock.correctAnswer")}</span>
                        {correctText(item, r.correct_response)}
                      </p>
                    </>
                  )}
                </>
              )}
              {isGroup ? null : ex?.text ? (
                <p className="font-semibold">{ex.text}</p>
              ) : ex?.limit ? (
                <p className="font-semibold">
                  {t("lesson.explainLimit")}{" "}
                  {canBuy && (
                    <Link href="/premium/" className="underline">
                      {t("mock.premiumGo")}
                    </Link>
                  )}
                </p>
              ) : ex?.failed ? (
                <p className="font-semibold">{t("common.error")}</p>
              ) : (
                <button type="button" onClick={() => void ask(r.question_id)} disabled={ex?.busy} className="self-start font-extrabold text-blue-deep underline">
                  {ex?.busy ? t("lesson.explaining") : t("lesson.explain")}
                </button>
              )}
            </Card>
          </li>
        );
      })}
    </ol>
    </>
  );
}
