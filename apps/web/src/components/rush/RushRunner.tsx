"use client";
import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { ApiError } from "@dtmai/api-client";
import Link from "next/link";
import { Button, Icon, ProgressBar } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { isAnswered, QuestionBody, type Response } from "@/components/lesson/QuestionBody";
import { api, type FinishOut, type SessionOut } from "@/lib/api";
import { clock, useCountdown } from "@/lib/useCountdown";

const FLASH_MS = 450;
const TOTAL_S = 60;

/** 60 s timed runner: answer submits at once, right/wrong flashes, next question follows immediately. */
export function RushRunner({ session, onDone }: { session: SessionOut; onDone: (r: FinishOut) => void }) {
  const t = useT();
  const reduce = useReducedMotion();
  const left = useCountdown(session.ends_at);
  const [i, setI] = useState(0);
  const [value, setValue] = useState<Response | null>(null);
  const [flash, setFlash] = useState<boolean | null>(null);
  const [streak, setStreak] = useState(0);
  const [points, setPoints] = useState(0);
  const [pending, setPending] = useState(false);
  const [finishFailed, setFinishFailed] = useState(false);
  const finishing = useRef(false);
  const started = useRef(Date.now());
  const item = session.items[i];

  const finish = async () => {
    if (finishing.current) return;
    finishing.current = true;
    setFinishFailed(false);
    try {
      onDone(await api.unwrap(api.client.POST("/v1/learning/sessions/{session_id}/finish", { params: { path: { session_id: session.id } } })));
    } catch {
      finishing.current = false;
      setFinishFailed(true);
    }
  };

  const submit = async (v: Response) => {
    if (!item || pending || flash !== null || finishing.current) return;
    setPending(true);
    try {
      const r = await api.unwrap(
        api.client.POST("/v1/learning/sessions/{session_id}/answers", {
          params: { path: { session_id: session.id } },
          body: { question_id: item.id, response: v, time_ms: Date.now() - started.current },
        }),
      );
      setStreak(r.streak ?? 0);
      setPoints(r.points ?? 0);
      setFlash(r.correct);
      window.setTimeout(() => {
        setFlash(null);
        setValue(null);
        started.current = Date.now();
        if (i + 1 >= session.items.length) void finish();
        else setI(i + 1);
      }, FLASH_MS);
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) void finish();
    } finally {
      setPending(false);
    }
  };

  // Single-choice answers go in on tap; everything else needs the check button / Enter.
  const onChange = (v: Response) => {
    setValue(v);
    if (item?.kind === "single_choice") void submit(v);
  };

  useEffect(() => {
    if (left === 0) void finish();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [left]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Enter" && item && value && isAnswered(item, value)) void submit(value);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item, value, flash, pending]);

  const urgent = left <= 10;
  return (
    <main className="mx-auto flex min-h-dvh max-w-2xl flex-col gap-4 p-4">
      <header className="flex items-center gap-3">
        <Link href="/practice/" aria-label={t("lesson.exit")} className="grid size-11 shrink-0 place-items-center rounded-xl text-ink-soft hover:bg-snow">
          <Icon name="close" />
        </Link>
        <div className="flex-1">
          <ProgressBar value={left} max={TOTAL_S} />
        </div>
        <span className={`w-16 text-right text-xl font-extrabold tabular-nums ${urgent ? "text-red-deep" : "text-ink"}`} role="timer" aria-label={t("rush.time")}>
          {clock(left)}
        </span>
      </header>
      <div className="flex items-center justify-between font-extrabold text-ink">
        <motion.span key={streak} initial={reduce ? false : { scale: 1.4 }} animate={{ scale: 1 }}>
          {t("rush.streak", { n: streak })}
        </motion.span>
        <span>{t("rush.score", { n: points })}</span>
      </div>
      {finishFailed && (
        <div role="alert" className="flex flex-col items-center gap-3 rounded-3xl border-2 border-red-deep bg-red-soft p-4 text-center">
          <p className="font-bold text-red-deep">{t("common.error")}</p>
          <Button onClick={() => void finish()}>{t("common.retry")}</Button>
        </div>
      )}
      {item && !finishFailed && (
        <motion.div
          key={item.id}
          initial={reduce ? false : { opacity: 0, x: 24 }}
          animate={{ opacity: 1, x: 0 }}
          className={`flex flex-col gap-4 rounded-3xl border-2 p-3 ${flash === null ? "border-transparent" : flash ? "border-brand bg-brand-soft" : "border-red-deep bg-red-soft"}`}
        >
          <QuestionBody item={item} value={value} onChange={onChange} disabled={pending || flash !== null} />
          {item.kind !== "single_choice" && (
            <Button disabled={!isAnswered(item, value) || pending || flash !== null} onClick={() => value && void submit(value)}>
              {t("common.check")}
            </Button>
          )}
        </motion.div>
      )}
    </main>
  );
}
