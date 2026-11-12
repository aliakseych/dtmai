"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@dtmai/api-client";
import { Button, buttonClass, ConfirmModal, HeartsStat, Mascot, ProgressBar, Sheet, Icon } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { GoalRing } from "@/components/GoalRing";
import { RichText } from "@/components/RichText";
import { api, type AnswerOut, type FinishOut, type ItemOut, type SessionOut, type Stats } from "@/lib/api";
import { useBilling } from "@/lib/billing";
import { refreshStats } from "@/lib/stats";
import { useTmaBackButton } from "@/lib/tma";
import { useAsync } from "@/lib/useAsync";
import { TheoryCards, type TheoryCard } from "./TheoryCards";
import { isTheorySeen, markTheorySeen } from "./theorySeen";
import { useLessonTheory } from "./useLessonTheory";
import { HeartsGate } from "./HeartsGate";
import { correctText, isAnswered, QuestionBody, type Response } from "./QuestionBody";

type Phase = "answering" | "feedback" | "done";
const isClosed = (e: unknown) => e instanceof ApiError && e.status === 409 && e.code === "session_closed";
const isNoHearts = (e: unknown) => e instanceof ApiError && e.status === 409 && e.code === "no_hearts";

/** Lesson/drill/review/placement runner: CHECK -> feedback sheet -> CONTINUE. Hearts apply to lesson and drill only. */
export function LessonPlayer({ load, exitHref, doneHref, lessonId }: { load: () => Promise<SessionOut>; exitHref: string; doneHref?: string; lessonId?: string }) {
  // The session id lives in the URL (?s=) so a reload or the hearts gate resumes it instead of starting over.
  const resumeId = useRef<string | null>(typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("s"));
  // Effects run twice under StrictMode: concurrent starts share one in-flight request so only one session is created.
  const pending = useRef<{ load: () => Promise<SessionOut>; p: Promise<SessionOut> } | null>(null);
  const start = useCallback(() => {
    if (pending.current?.load === load) return pending.current.p;
    const p = begin();
    pending.current = { load, p };
    const clear = () => {
      if (pending.current?.p === p) pending.current = null;
    };
    p.then(clear, clear);
    return p;
    async function begin() {
    const sid = resumeId.current;
    if (sid) {
      try {
        const s = await api.unwrap(api.client.GET("/v1/learning/sessions/{session_id}", { params: { path: { session_id: sid } } }));
        if (s.status === "in_progress") return s;
      } catch {
        /* unknown, foreign or closed session: start a new one */
      }
      resumeId.current = null;
    }
    const s = await load();
    const url = new URL(window.location.href);
    url.searchParams.set("s", s.id);
    window.history.replaceState(window.history.state, "", url);
    return s;
    }
  }, [load]);
  const { state, reload } = useAsync(start, [start]);
  // The session was closed elsewhere (e.g. by a duplicate start): drop it from the URL and begin a fresh one.
  const restart = useCallback(() => {
    resumeId.current = null;
    const url = new URL(window.location.href);
    url.searchParams.delete("s");
    window.history.replaceState(window.history.state, "", url);
    reload();
  }, [reload]);
  if (state.status === "error" && isNoHearts(state.error)) return <HeartsGate exitHref={exitHref} onRetry={reload} />;
  return (
    <AsyncView state={state} onRetry={reload} exitHref={exitHref} isEmpty={(s) => s.items.length === 0 && s.answered === 0}>
      {(s) => <TheoryFirst session={s} onRestart={restart} lessonId={lessonId} exitHref={exitHref} doneHref={doneHref ?? exitHref} />}
    </AsyncView>
  );
}

/** A lesson with theory shows its cards once per device before the first question; the same cards stay reachable from the wrong-answer sheet. */
function TheoryFirst({ session, lessonId, exitHref, doneHref, onRestart }: { onRestart: () => void; session: SessionOut; lessonId?: string; exitHref: string; doneHref: string }) {
  const t = useT();
  const theory = useLessonTheory(session.subject_id, lessonId);
  const [shown, setShown] = useState(false);
  if (theory === undefined) return <div className="min-h-dvh" aria-busy="true" />;
  if (lessonId && theory.length > 0 && !shown && session.answered === 0 && !isTheorySeen(lessonId))
    return (
      <TheoryCards
        cards={theory}
        doneLabel={t("theory.startPractice")}
        onDone={() => {
          markTheorySeen(lessonId);
          setShown(true);
        }}
      />
    );
  return <Runner session={session} onRestart={onRestart} exitHref={exitHref} doneHref={doneHref} theory={theory} />;
}

function Runner({ session, exitHref, doneHref, theory, onRestart }: { onRestart: () => void; session: SessionOut; exitHref: string; doneHref: string; theory?: TheoryCard[] }) {
  const [theoryOpen, setTheoryOpen] = useState(false);
  const t = useT();
  const router = useRouter();
  const { canBuy } = useBilling();
  const costs = session.mode === "lesson" || session.mode === "drill";
  const [queue, setQueue] = useState<ItemOut[]>(session.items);
  const [index, setIndex] = useState(0);
  const [value, setValue] = useState<Response | null>(null);
  const [phase, setPhase] = useState<Phase>("answering");
  const [result, setResult] = useState<AnswerOut | null>(null);
  const [hearts, setHearts] = useState<number | null>(session.hearts);
  const [unlimited, setUnlimited] = useState(session.unlimited_hearts);
  const [summary, setSummary] = useState<FinishOut | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [streakShown, setStreakShown] = useState(false);
  const [gate, setGate] = useState(false);
  const [exit, setExit] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const [closed, setClosed] = useState(false);
  const [report, setReport] = useState<"idle" | "busy" | "sent">("idle");
  const [explain, setExplain] = useState<{ text?: string; limit?: boolean; guest?: boolean; failed?: boolean } | null>(null);
  const started = useRef(Date.now());
  const main = useRef<HTMLElement>(null);

  const q = queue[index];
  const answered = q ? isAnswered(q, value) : false;
  const askExit = useCallback(() => setExit(true), []);
  useTmaBackButton(askExit);

  const check = useCallback(async () => {
    if (!q || !value || !answered || busy) return;
    setBusy(true);
    setError(false);
    try {
      const r = await api.unwrap(
        api.client.POST("/v1/learning/sessions/{session_id}/answers", {
          params: { path: { session_id: session.id } },
          body: { question_id: q.id, response: value, time_ms: Date.now() - started.current },
        }),
      );
      setResult(r);
      setHearts(r.hearts);
      void refreshStats().catch(() => undefined);
      setUnlimited(r.unlimited_hearts);
      if (r.next_item && !queue.some((x) => x.id === r.next_item!.id)) setQueue((x) => [...x, r.next_item!]);
      setPhase("feedback");
    } catch (e) {
      if (isNoHearts(e)) setGate(true);
      else if (isClosed(e)) setClosed(true);
      else setError(true);
    } finally {
      setBusy(false);
    }
  }, [q, value, answered, busy, session.id, queue]);

  const finish = useCallback(async () => {
    setBusy(true);
    try {
      const f = await api.unwrap(api.client.POST("/v1/learning/sessions/{session_id}/finish", { params: { path: { session_id: session.id } } }));
      setSummary(f);
      setPhase("done");
      refreshStats().then(setStats, () => undefined);
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }, [session.id]);

  const next = useCallback(async () => {
    // A finished session ends here even at 0 hearts; the gate only blocks while questions remain.
    if (result?.session_done || index + 1 >= queue.length) return finish();
    const out = costs && !unlimited && hearts !== null && hearts <= 0 && !result?.correct;
    if (out) return setGate(true);
    setIndex(index + 1);
    setValue(null);
    setResult(null);
    setExplain(null);
    setReport("idle");
    setPhase("answering");
    started.current = Date.now();
  }, [costs, unlimited, hearts, result, index, queue.length, finish]);

  // A resumed session with nothing left to answer is just closed out.
  const closing = useRef(false);
  useEffect(() => {
    if (!q && phase === "answering" && !closing.current) {
      closing.current = true;
      void finish();
    }
  }, [q, phase, finish]);

  async function leave() {
    if (phase !== "done") {
      try {
        await api.client.POST("/v1/learning/sessions/{session_id}/finish", { params: { path: { session_id: session.id } } });
      } catch {
        /* leaving anyway; the session stays resumable */
      }
      void refreshStats().catch(() => undefined);
    }
    router.push(exitHref);
  }

  async function reportIt() {
    if (!q) return;
    setReport("busy");
    try {
      await api.unwrap(api.client.POST("/v1/bank/questions/{question_id}/report", { params: { path: { question_id: q.id } }, body: { reason: "" } }));
      setReport("sent");
    } catch {
      setReport("idle");
      setError(true);
    }
  }

  // Enter = CHECK / CONTINUE (ignored on buttons/links so it never double-fires); focus follows the phase.
  useEffect(() => {
    if (phase === "done" || gate || exit || theoryOpen) return;
    const h = (e: KeyboardEvent) => {
      if (e.key !== "Enter" || (e.target as HTMLElement).closest("button,a")) return;
      e.preventDefault();
      if (phase === "answering") void check();
      else void next();
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [phase, gate, exit, theoryOpen, check, next]);
  useEffect(() => {
    if (phase === "answering") main.current?.querySelector<HTMLElement>("[data-option],input,select")?.focus({ preventScroll: true });
  }, [index, phase]);

  async function explainIt() {
    if (!q) return;
    setExplain({});
    try {
      const r = await api.unwrap(api.client.POST("/v1/ai/explain/{question_id}", { params: { path: { question_id: q.id } } }));
      setExplain({ text: r.explanation });
    } catch (e) {
      setExplain(
        e instanceof ApiError && e.status === 403
          ? { guest: true }
          : e instanceof ApiError && [402, 429].includes(e.status)
            ? { limit: true }
            : { failed: true },
      );
    }
  }

  if (gate) return <HeartsGate exitHref={exitHref} subjectId={session.subject_id} onRetry={() => window.location.reload()} />;

  if (phase === "done" && summary) {
    const showStreak = !streakShown && stats && stats.streak > 0 && stats.streak_active_today && session.mode !== "placement";
    if (showStreak)
      return (
        <div className="flex min-h-dvh flex-col items-center justify-center gap-4 px-4 text-center">
          <Mascot mood="streak" size={220} alt="" className="pop-in h-auto w-48" />
          <h1 className="text-3xl">{t("celebrate.streak", { n: stats.streak })}</h1>
          <GoalRing done={stats.today_xp} goal={stats.daily_goal_xp} size={88} />
          <Button className="max-w-xs" block onClick={() => setStreakShown(true)}>
            {t("common.continue")}
          </Button>
        </div>
      );
    return (
      <div className="flex min-h-dvh flex-col items-center justify-center gap-4 px-4 text-center">
        <Mascot mood={summary.total > 0 && summary.correct * 2 < summary.total ? "sad" : "celebrate"} size={220} alt="" className="pop-in h-auto w-48" />
        <h1 className="text-3xl">{session.mode === "lesson" || session.mode === "placement" ? t("lesson.done") : t("lesson.drillDone")}</h1>
        <p className="text-lg text-ink-soft">
          +{summary.xp_base} {t("stat.xp")} · {summary.correct}/{summary.total}
        </p>
        {summary.mode === "placement" && summary.start_unit_index !== null && <p className="font-bold">{t("celebrate.placement", { n: summary.start_unit_index + 1 })}</p>}
        <Link href={doneHref} className={buttonClass("primary", true, "max-w-xs")}>
          {t("common.continue")}
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-dvh max-w-3xl flex-col px-4">
      <header className="flex items-center gap-4 py-5">
        <button type="button" aria-label={t("lesson.exit")} className="grid size-10 shrink-0 place-items-center rounded-xl text-ink-soft hover:bg-snow" onClick={askExit}>
          <Icon name="close" />
        </button>
        <ProgressBar value={Math.min(session.answered + index + (phase === "feedback" ? 1 : 0), result?.total ?? session.total)} max={result?.total ?? session.total} label={t("lesson.progress")} />
        {costs && <HeartsStat value={unlimited ? "∞" : (hearts ?? 0)} label={t("stat.hearts")} />}
      </header>

      <main ref={main} className="flex flex-1 flex-col gap-5 pb-56">
        {q && <QuestionBody key={q.id} item={q} value={value} onChange={setValue} disabled={phase !== "answering"} correct={phase === "feedback" ? (result?.correct_response ?? null) : null} wasCorrect={result?.correct} />}
        {closed && (
          <div role="alert" className="flex flex-col items-start gap-2 font-bold text-red-deep">
            {t("common.error")}
            <Button variant="secondary" onClick={onRestart}>
              {t("common.retry")}
            </Button>
          </div>
        )}
        {error && (
          <p role="alert" className="font-bold text-red-deep">
            {t("common.error")}
          </p>
        )}
      </main>

      <div className="fixed inset-x-0 bottom-0 bg-white">
        {phase === "feedback" && result && q ? (
          <Sheet
            tone={result.correct ? "correct" : "incorrect"}
            title={result.correct ? t("lesson.correct") : t("lesson.incorrect")}
            mascot={<Mascot mood={result.correct ? "celebrate" : "sad"} size={64} alt="" className="hidden h-auto w-14 sm:block" />}
            action={
              <Button autoFocus variant={result.correct ? "primary" : "danger"} block onClick={next} disabled={busy}>
                {t("common.continue")}
              </Button>
            }
          >
            {!result.correct && (
              <p>
                <strong>
                  <RichText text={correctText(q, result.correct_response)} />
                </strong>
              </p>
            )}
            {explain?.text ? (
              <p className="mt-1 font-semibold">
                <RichText text={explain.text} />
              </p>
            ) : explain?.guest ? (
              <p className="mt-1 font-semibold">
                {t("lesson.explainGuest")}{" "}
                <Link href="/register/" className="underline">{t("lesson.explainSignUp")}</Link>
              </p>
            ) : explain?.limit ? (
              <p className="mt-1 font-semibold">
                {t("lesson.explainLimit")} {canBuy && <Link href="/premium/" className="underline">{t("hearts.premium")}</Link>}
              </p>
            ) : explain?.failed ? (
              <p className="mt-1 font-semibold">{t("common.error")}</p>
            ) : (
              <button type="button" onClick={explainIt} disabled={!!explain} className="mt-1 font-extrabold underline">
                {explain ? t("lesson.explaining") : t("lesson.explain")}
              </button>
            )}
            {!result.correct && theory && theory.length > 0 && (
              <div className="mt-1">
                <button type="button" onClick={() => setTheoryOpen(true)} className="font-extrabold underline">
                  {t("theory.see")}
                </button>
              </div>
            )}
            <div className="mt-1">
              {report === "sent" ? (
                <span className="text-sm font-semibold text-ink-soft">{t("lesson.reported")}</span>
              ) : (
                <button type="button" onClick={reportIt} disabled={report === "busy"} className="text-sm font-bold text-ink-soft underline">
                  {t("lesson.report")}
                </button>
              )}
            </div>
          </Sheet>
        ) : (
          <div className="mx-auto max-w-3xl border-t-2 border-line px-4 pt-5 pb-[max(1.25rem,env(safe-area-inset-bottom))]">
            <Button block disabled={!answered || busy} onClick={check}>
              {t("common.check")}
            </Button>
          </div>
        )}
      </div>

      <ConfirmModal open={exit} title={t("lesson.exitTitle")} message={t("lesson.quit")} confirmLabel={t("lesson.exit")} cancelLabel={t("lesson.stay")} danger onConfirm={leave} onClose={() => setExit(false)} />
      {theoryOpen && theory && <TheoryCards cards={theory} title={t("theory.title")} onDone={() => setTheoryOpen(false)} />}
    </div>
  );
}
