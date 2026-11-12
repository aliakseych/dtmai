"use client";
import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Button, cn, Mascot } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { correctText, isAnswered, QuestionBody, type Response } from "@/components/lesson/QuestionBody";
import type { ItemOut } from "@/lib/api";
import { answerDailyQuestion, getDailyQuestions, type DailyAnswerOut, type DailyQuestionOut } from "@/lib/planner";
import { useAsync } from "@/lib/useAsync";
import { ApiError } from "@dtmai/api-client";

/** Daily questions carry no passage/type info; QuestionBody only reads the shared fields. */
const asItem = (q: DailyQuestionOut) => ({ ...q, passage_id: null, children: [] }) as unknown as ItemOut;

/** OnePrep-style card: one question at a time, instant feedback, dots for progress. */
export function DailyQuestions() {
  const t = useT();
  const { state, reload } = useAsync(getDailyQuestions, []);
  // No plan yet: the countdown card already prompts to pick a field; nothing to practise.
  if (state.status === "error" && state.error instanceof ApiError && state.error.code === "plan_not_found") return null;
  if (state.status === "ready" && state.data.questions.length === 0) return null;
  return (
    <section className="flex flex-col gap-2" aria-label={t("plan.home.dailyQuestions")}>
      <h2 className="text-lg">{t("plan.home.dailyQuestions")}</h2>
      <AsyncView state={state} onRetry={reload}>
        {(d) => <Deck questions={d.questions} />}
      </AsyncView>
    </section>
  );
}

function Deck({ questions }: { questions: DailyQuestionOut[] }) {
  const t = useT();
  const reduce = useReducedMotion();
  const [idx, setIdx] = useState(0);
  const [value, setValue] = useState<Response | null>(null);
  const [results, setResults] = useState<(DailyAnswerOut | undefined)[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);

  const finished = idx >= questions.length;
  const q = finished ? null : questions[idx];
  const item = q ? asItem(q) : null;
  const result = results[idx];
  const score = results.filter((r) => r?.correct).length;

  const check = async () => {
    if (!q || !value || busy) return;
    setBusy(true);
    setError(false);
    try {
      const r = await answerDailyQuestion(q.id, value);
      setResults((prev) => Object.assign([...prev], { [idx]: r }));
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  };
  const next = () => {
    setValue(null);
    setIdx((i) => i + 1);
  };

  return (
    <div className="flex flex-col gap-4 rounded-card border-2 border-line bg-white p-4">
      <ol className="flex gap-1.5" aria-hidden="true">
        {questions.map((x, i) => {
          const r = results[i];
          return (
            <motion.li
              key={x.id}
              animate={reduce ? undefined : { scaleY: r ? [1, 1.8, 1] : 1, opacity: r || i === idx ? 1 : 0.7 }}
              transition={{ duration: 0.35 }}
              className={cn("h-2.5 min-w-0 flex-1 rounded-full transition-colors", r ? (r.correct ? "bg-accent" : "bg-red") : i === idx ? "bg-brand" : "bg-line")}
            />
          );
        })}
      </ol>
      <AnimatePresence mode="wait" initial={false}>
        {finished || !q || !item ? (
          <motion.div key="done" initial={reduce ? false : { opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="flex flex-col items-center gap-2 py-2 text-center">
            <Mascot mood="wave" size={96} alt="" className="h-auto w-20" />
            <p className="text-xl font-extrabold">
              {score} / {questions.length}
            </p>
            <p className="font-bold text-ink-soft">{t("quests.done")}</p>
          </motion.div>
        ) : (
          <motion.div key={q.id} initial={reduce ? false : { opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={reduce ? undefined : { opacity: 0, x: -24 }} transition={{ duration: 0.2 }} className="flex flex-col gap-4">
            <QuestionBody item={item} value={value} onChange={setValue} disabled={!!result || busy} correct={result?.correct_response ?? null} wasCorrect={result?.correct} />
            <AnimatePresence>
              {result && (
                <motion.div
                  role="status"
                  initial={reduce ? false : { opacity: 0, y: 12 }}
                  animate={result.correct && !reduce ? { opacity: 1, y: 0, scale: [1, 1.04, 1] } : !result.correct && !reduce ? { opacity: 1, y: 0, x: [0, -8, 8, -4, 4, 0] } : { opacity: 1, y: 0 }}
                  className={cn("flex items-center gap-3 rounded-2xl border-2 p-3 font-extrabold", result.correct ? "border-accent bg-accent-soft" : "border-red bg-white text-red")}
                >
                  <Mascot mood={result.correct ? "celebrate" : "sad"} size={48} alt="" className="h-auto w-12 shrink-0" />
                  <span className="min-w-0 break-words">{result.correct ? t("lesson.correct") : `${t("lesson.incorrect")} ${correctText(item, result.correct_response)}`}</span>
                </motion.div>
              )}
            </AnimatePresence>
            {error && <p role="alert" className="text-sm font-bold text-red">{t("common.retry")}</p>}
            {result ? (
              <Button block onClick={next}>
                {t("common.continue")}
              </Button>
            ) : (
              <Button block disabled={!isAnswered(item, value) || busy} onClick={check}>
                {t("common.check")}
              </Button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
