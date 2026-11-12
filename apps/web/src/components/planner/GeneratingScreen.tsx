"use client";
import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { ApiError } from "@dtmai/api-client";
import { Button, Mascot } from "@dtmai/ui";
import { useT, type MessageKey } from "@dtmai/i18n";
import { BouncyCheck } from "./parts";

const ITEMS: MessageKey[] = ["plan.gen.s1", "plan.gen.s2", "plan.gen.s3", "plan.gen.s4", "plan.gen.s5"];
const STEP_MS = 700;

/**
 * Runs the create request while a checklist ticks one item at a time; leaves only when both the
 * checklist and the request are done, so the animation never gets cut short or lies about success.
 */
export function GeneratingScreen({ request, onDone, onBack }: { request: () => Promise<unknown>; onDone: () => void; onBack: () => void }) {
  const t = useT();
  const reduce = useReducedMotion();
  const [ticked, setTicked] = useState(0);
  const [result, setResult] = useState<"pending" | "ok" | ApiError | Error>("pending");
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    request().then(
      () => setResult("ok"),
      (e: Error) => setResult(e),
    );
  }, [request]);

  const failed = result !== "pending" && result !== "ok";
  useEffect(() => {
    if (failed || ticked >= ITEMS.length) return;
    const id = setTimeout(() => setTicked((n) => n + 1), reduce ? 150 : STEP_MS);
    return () => clearTimeout(id);
  }, [ticked, failed, reduce]);

  const finished = result === "ok" && ticked >= ITEMS.length;
  useEffect(() => {
    if (!finished) return;
    const id = setTimeout(onDone, reduce ? 200 : 900);
    return () => clearTimeout(id);
  }, [finished, onDone, reduce]);

  if (failed) {
    return (
      <div role="alert" className="mx-auto flex min-h-dvh max-w-xl flex-col items-center justify-center gap-4 px-4 text-center">
        <Mascot mood="sad" size={140} alt="" className="h-auto w-28" />
        <p className="text-xl font-extrabold">{t("plan.gen.failed")}</p>
        {result instanceof ApiError && result.problem?.title && <p className="text-sm text-ink-soft">{result.problem.title}</p>}
        <Button block onClick={onBack}>
          {t("common.retry")}
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-dvh max-w-xl flex-col items-center justify-center gap-6 px-4" aria-busy={!finished}>
      <Mascot mood={finished ? "celebrate" : "calendar"} size={160} alt={t("mascot.alt")} className="h-auto w-32" />
      <h1 className="text-center text-2xl">{finished ? t("plan.gen.done") : t("plan.gen.title")}</h1>
      <ul className="flex w-full flex-col gap-2" aria-live="polite">
        {ITEMS.map((k, i) => {
          const done = i < ticked;
          return (
            <motion.li
              key={k}
              initial={reduce ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: done || i === ticked ? 1 : 0.45, y: 0 }}
              transition={{ delay: reduce ? 0 : 0.05 * i }}
              className="flex items-center gap-3 rounded-card border-2 border-line bg-white p-3 font-extrabold"
            >
              {done ? <BouncyCheck /> : <span aria-hidden="true" className="size-7 shrink-0 rounded-full border-2 border-line" />}
              <span>{t(k)}</span>
            </motion.li>
          );
        })}
      </ul>
    </div>
  );
}
