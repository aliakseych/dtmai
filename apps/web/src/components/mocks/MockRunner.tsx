"use client";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button, ConfirmModal, Icon } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { isAnswered, QuestionBody, type Response } from "@/components/lesson/QuestionBody";
import { api, type Attempt } from "@/lib/api";
import { clock, useCountdown } from "@/lib/useCountdown";
import { useTmaBackButton, withTmaReauth } from "@/lib/tma";
import { useAsync } from "@/lib/useAsync";
import { QuestionNavigator } from "./QuestionNavigator";
import { SaveIndicator } from "./SaveIndicator";
import { useAutosave } from "./useAutosave";
import { useSubjectNames } from "./useSubjectNames";
import { toItems } from "./items";

const LOW_SECONDS = 300;

/** Full-screen timed mock: navigator, mark-for-review, debounced autosave, guarded submit. */
export function MockRunner({ attemptId }: { attemptId: string }) {
  const { state, reload } = useAsync(() => api.unwrap(api.client.GET("/v1/assessment/attempts/{attempt_id}", { params: { path: { attempt_id: attemptId } } })), [attemptId]);
  const router = useRouter();
  const submitted = state.status === "ready" && state.data.status === "submitted";
  // A submitted attempt has no live exam: go to its result.
  useEffect(() => {
    if (submitted) router.replace(`/mocks/result/?attempt=${attemptId}`);
  }, [submitted, router, attemptId]);
  return (
    <AsyncView state={state} onRetry={reload}>
      {(attempt) => (attempt.status === "submitted" ? null : <Run key={attempt.id} attempt={attempt} />)}
    </AsyncView>
  );
}

function Run({ attempt }: { attempt: Attempt }) {
  const t = useT();
  const router = useRouter();
  const { name } = useSubjectNames();
  const items = useMemo(() => toItems(attempt.items), [attempt.items]);
  const resultHref = `/mocks/result/?attempt=${attempt.id}`;

  const [answers, setAnswers] = useState<Record<string, Response>>(() => ({ ...attempt.answers }));
  const [flags, setFlags] = useState<string[]>(attempt.flags);
  // Resume at the first unanswered question.
  const [index, setIndex] = useState(() => {
    const i = items.findIndex((it) => !isAnswered(it, attempt.answers[it.id] ?? null));
    return i < 0 ? 0 : i;
  });
  const [navOpen, setNavOpen] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [exit, setExit] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<"save" | "submit" | null>(null);
  const [expired, setExpired] = useState(false);
  const submitted = useRef(false);
  const main = useRef<HTMLElement>(null);

  // Deadline on the local clock, corrected for client/server skew measured at load.
  const [deadline] = useState(() => new Date(Date.parse(attempt.deadline) - (Date.parse(attempt.server_now) - Date.now())).toISOString());
  const left = useCountdown(deadline);

  // manual: flush first (failure shows retry / submit anyway); force: submit what the server holds; auto: time is up.
  const submit = useCallback(
    async (mode: "manual" | "force" | "auto") => {
      if (submitted.current) return;
      submitted.current = true;
      setSubmitting(true);
      setError(null);
      // A refused save because the deadline passed is not a failure: the server submits what it holds.
      if (mode === "manual" && !(await save.flush()) && !save.wasRejected()) {
        submitted.current = false;
        setSubmitting(false);
        setConfirm(false);
        setError("save");
        return;
      }
      // Time is up: send the pending answers first so the grace window is used; a failure still submits.
      if (mode === "auto") await save.flush();
      try {
        await withTmaReauth(() => api.unwrap(api.client.POST("/v1/assessment/attempts/{attempt_id}/submit", { params: { path: { attempt_id: attempt.id } } })));
        router.replace(mode === "auto" ? `${resultHref}&auto=1` : resultHref);
      } catch {
        submitted.current = false;
        setSubmitting(false);
        setConfirm(false);
        setError("submit");
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [attempt.id, resultHref, router],
  );

  const save = useAutosave(attempt.id, () => {
    setExpired(true);
    void submit("auto");
  });

  // Time is up: submit whatever the server holds.
  useEffect(() => {
    if (left === 0) void submit("auto");
  }, [left, submit]);

  // Unsaved edits are also sent with keepalive on pagehide/unmount; the prompt only guards edits that are still pending.
  useEffect(() => {
    const guard = (e: BeforeUnloadEvent) => {
      if (submitted.current || !save.dirty()) return;
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", guard);
    return () => window.removeEventListener("beforeunload", guard);
  }, [save]);

  const askExit = useCallback(() => setExit(true), []);
  useTmaBackButton(askExit);

  useEffect(() => main.current?.focus(), [index]);

  const item = items[index];
  const cells = useMemo(() => items.map((it) => ({ id: it.id, answered: isAnswered(it, answers[it.id] ?? null), flagged: flags.includes(it.id) })), [items, answers, flags]);
  const unanswered = cells.filter((c) => !c.answered).length;

  function onChange(v: Response) {
    setAnswers((a) => ({ ...a, [item.id]: v }));
    save.queue({ answers: { [item.id]: v } });
  }
  function toggleFlag() {
    const next = flags.includes(item.id) ? flags.filter((f) => f !== item.id) : [...flags, item.id];
    setFlags(next);
    save.queue({ answers: {}, flags: next });
  }
  const go = (i: number) => {
    setIndex(i);
    setNavOpen(false);
  };

  if (!item) return null;
  const flagged = flags.includes(item.id);
  const low = left <= LOW_SECONDS;

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-white pt-[env(safe-area-inset-top)]">
      <header className="flex items-center gap-2 border-b-2 border-line px-4 py-3 sm:gap-3">
        <button type="button" onClick={() => setExit(true)} aria-label={t("common.close")} className="grid size-10 shrink-0 place-items-center rounded-xl border-2 border-line text-ink-soft">
          <Icon name="close" size={20} />
        </button>
        <div role="timer" aria-label={t("mock.timer")} className={`rounded-xl px-3 py-1 text-xl font-extrabold tabular-nums ${low ? "bg-red-soft text-red-deep" : "bg-snow text-ink"}`}>
          {clock(left)}
        </div>
        <div className="flex-1" />
        <SaveIndicator state={save.state} onRetry={() => void save.flush()} />
        <Button onClick={() => setConfirm(true)} disabled={submitting} className="shrink-0">
          {t("mock.submit")}
        </Button>
      </header>

      {expired && (
        <p role="alert" className="bg-accent px-4 py-2 text-center font-bold text-ink">
          {t("mock.expired")}
        </p>
      )}
      {error === "submit" && (
        <p role="alert" className="flex flex-wrap items-center justify-center gap-3 bg-red-soft px-4 py-2 text-center font-bold text-red-deep">
          {t("mock.submitError")}
          <button type="button" className="underline" onClick={() => void submit(left === 0 ? "auto" : "manual")}>
            {t("mock.retry")}
          </button>
        </p>
      )}
      {error === "save" && (
        <p role="alert" className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 bg-red-soft px-4 py-2 text-center font-bold text-red-deep">
          {t("mock.submitSaveError")}
          <span className="flex gap-4">
            <button type="button" className="underline" onClick={() => void submit("manual")}>
              {t("mock.retry")}
            </button>
            <button type="button" className="underline" onClick={() => void submit("force")}>
              {t("mock.submitAnyway")}
            </button>
          </span>
        </p>
      )}

      <div className="flex min-h-0 flex-1">
        <main ref={main} tabIndex={-1} className="mx-auto flex min-w-0 flex-1 flex-col gap-5 overflow-y-auto px-4 py-6 outline-none lg:max-w-3xl">
          <div className="flex flex-wrap items-center justify-between gap-2 text-sm font-bold uppercase text-ink-soft">
            <span>{t("mock.question", { n: index + 1, total: items.length })}</span>
            <span>{name(item.subject_id)}</span>
          </div>
          <QuestionBody key={item.id} item={item} value={answers[item.id] ?? null} onChange={onChange} disabled={submitting} />
          <div>
            <button
              type="button"
              aria-pressed={flagged}
              onClick={toggleFlag}
              className={`inline-flex items-center gap-2 rounded-xl border-2 px-3 py-2 font-bold ${flagged ? "border-ink bg-ink text-white" : "border-line text-ink-soft"}`}
            >
              <Icon name="flag" size={20} />
              {flagged ? t("mock.unflag") : t("mock.flag")}
            </button>
          </div>
        </main>
        <aside className={`${navOpen ? "block" : "hidden"} absolute inset-x-0 bottom-[4.5rem] z-10 max-h-[60%] overflow-y-auto border-t-2 border-line bg-white p-4 lg:static lg:block lg:max-h-none lg:w-80 lg:border-l-2 lg:border-t-0`}>
          <h2 className="mb-3 text-sm uppercase text-ink-soft">{t("mock.nav")}</h2>
          <QuestionNavigator cells={cells} current={index} onGo={go} />
        </aside>
      </div>

      <footer className="grid grid-cols-3 gap-2 border-t-2 border-line px-4 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] lg:flex lg:items-center">
        <Button variant="secondary" className="min-w-0 !px-2 lg:!px-5" disabled={index === 0} onClick={() => go(index - 1)}>
          {t("mock.prev")}
        </Button>
        <Button variant="secondary" className="min-w-0 !px-2 lg:hidden" aria-expanded={navOpen} onClick={() => setNavOpen((o) => !o)}>
          {t("mock.nav")}
        </Button>
        <div className="hidden flex-1 lg:block" />
        {/* The header already carries the one submit button; the last question just has no "next". */}
        {index < items.length - 1 ? <Button className="min-w-0 !px-2 lg:!px-5" onClick={() => go(index + 1)}>{t("mock.next")}</Button> : <span aria-hidden="true" />}
      </footer>

      <ConfirmModal
        open={confirm}
        title={t("mock.submitTitle")}
        message={unanswered > 0 ? t("mock.submitUnanswered", { n: unanswered }) : t("mock.submitAll")}
        confirmLabel={submitting ? t("mock.submitting") : t("mock.submitConfirm")}
        cancelLabel={t("mock.keepGoing")}
        onConfirm={() => void submit("manual")}
        onClose={() => !submitting && setConfirm(false)}
      />
      <ConfirmModal open={exit} title={t("mock.exitTitle")} message={t("mock.exitMsg")} confirmLabel={t("mock.exitConfirm")} cancelLabel={t("mock.keepGoing")} danger onConfirm={() => void save.flush().finally(() => { submitted.current = true; router.replace("/mocks/"); })} onClose={() => setExit(false)} />
    </div>
  );
}
