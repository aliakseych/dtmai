"use client";
import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import Link from "next/link";
import { ApiError } from "@dtmai/api-client";
import { Button, Mascot, buttonClass } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { PageTitle } from "@/components/PageTitle";
import { RichText } from "@/components/RichText";
import { api, type TutorQuiz, type TutorQuota } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useAsync } from "@/lib/useAsync";
import { QuizCard } from "./QuizCard";

type Msg = { role: "user" | "assistant"; content: string; quiz?: TutorQuiz | null };
type Problem = "limit" | "locked" | "failed" | null;

function QuotaPill({ quota }: { quota: TutorQuota }) {
  const t = useT();
  const unlimited = quota.remaining < 0;
  return (
    <span className="rounded-full border-2 border-line px-3 py-1 text-sm font-extrabold text-ink" title={t("temur.quota")}>
      {unlimited ? t("temur.quota.unlimited") : t("temur.quota.left", { n: quota.remaining })}
    </span>
  );
}

function TemurChat() {
  const t = useT();
  const { locale } = useLocale();
  const reduce = useReducedMotion();
  const sug = useAsync(() => api.unwrap(api.client.GET("/v1/ai/tutor/suggestions", { params: { query: { locale } } })), [locale]);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<Problem>(null);
  const [quota, setQuota] = useState<TutorQuota | null>(null);
  const end = useRef<HTMLDivElement>(null);

  const q = quota ?? (sug.state.status === "ready" ? sug.state.data.quota : null);
  const exhausted = problem === "limit" || (q !== null && q.remaining === 0);

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "end" });
  }, [msgs, busy, reduce]);

  const send = async (raw: string) => {
    const content = raw.trim();
    if (!content || busy || exhausted) return;
    const next: Msg[] = [...msgs, { role: "user", content }];
    setMsgs(next);
    setText("");
    setProblem(null);
    setBusy(true);
    try {
      const r = await api.unwrap(
        api.client.POST("/v1/ai/tutor", { body: { messages: next.slice(-38).map(({ role, content: c }) => ({ role, content: c })), locale } }),
      );
      setMsgs([...next, { role: "assistant", content: r.reply, quiz: r.quiz }]);
      setQuota(r.quota);
    } catch (e) {
      setProblem(e instanceof ApiError && e.status === 429 ? "limit" : e instanceof ApiError && e.code === "tutor_locked_during_mock" ? "locked" : "failed");
      if (e instanceof ApiError && e.status === 429) setQuota((p) => (p ? { ...p, remaining: 0 } : p));
    } finally {
      setBusy(false);
    }
  };

  const chips = sug.state.status === "ready" ? sug.state.data.suggestions : [];
  const bubble = (m: Msg, i: number) => (
    <motion.div
      key={i}
      initial={reduce ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={m.role === "user" ? "flex justify-end" : "flex items-start gap-2"}
    >
      {m.role === "assistant" && <Mascot mood="straight" size={40} alt="" />}
      <div
        className={
          m.role === "user"
            ? "max-w-[85%] rounded-2xl border-2 border-b-4 border-ink bg-ink px-4 py-2 font-bold text-white"
            : "max-w-[85%] rounded-2xl border-2 border-b-4 border-line bg-white px-4 py-2 text-ink"
        }
      >
        <RichText text={m.content} />
        {m.quiz && <QuizCard quiz={m.quiz} />}
      </div>
    </motion.div>
  );

  return (
    <>
      <div className="flex items-center justify-between gap-3">
        <PageTitle>{t("temur.title")}</PageTitle>
        {q && <QuotaPill quota={q} />}
      </div>
      <div className="flex flex-col gap-4">
        {msgs.length === 0 && (
          <div className="flex flex-col items-center gap-3 text-center">
            <Mascot mood="wave" size={120} alt="" />
            <p className="text-ink-soft">{t("temur.hello")}</p>
            <div className="flex flex-wrap justify-center gap-2">
              {chips.map((c) => (
                <button
                  key={c}
                  type="button"
                  disabled={busy || exhausted}
                  onClick={() => void send(c)}
                  className="rounded-2xl border-2 border-b-4 border-line bg-white px-3 py-2 text-sm font-bold text-ink hover:bg-snow disabled:opacity-50"
                >
                  {c}
                </button>
              ))}
            </div>
          </div>
        )}
        <div className="flex flex-col gap-3" aria-live="polite">
          {msgs.map(bubble)}
          {busy && (
            <div className="flex items-center gap-2 text-ink-soft">
              <Mascot mood="thinking" size={40} alt="" />
              <span>{t("temur.thinking")}</span>
            </div>
          )}
          <div ref={end} />
        </div>
        {problem && (
          <p role="alert" className="font-bold text-red-deep">
            {problem === "limit" ? t("temur.limit") : problem === "locked" ? t("temur.locked") : t("common.error")}
          </p>
        )}
        {exhausted && !problem && <p className="font-bold text-ink-soft">{t("temur.limit")}</p>}
        <form
          className="sticky bottom-2 flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            void send(text);
          }}
        >
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={4000}
            disabled={exhausted}
            placeholder={t("temur.placeholder")}
            aria-label={t("temur.placeholder")}
            className="min-w-0 flex-1 rounded-2xl border-2 border-line bg-white px-4 py-3 text-ink"
          />
          <Button type="submit" disabled={busy || exhausted || !text.trim()}>
            {t("temur.send")}
          </Button>
        </form>
      </div>
    </>
  );
}

export function TemurView() {
  const t = useT();
  const { isGuest } = useAuth();
  if (!isGuest) return <TemurChat />;
  return (
    <>
      <PageTitle>{t("temur.title")}</PageTitle>
      <div className="flex flex-col items-center gap-3 text-center">
        <Mascot mood="wave" size={120} alt="" />
        <p className="text-ink-soft">{t("temur.guest")}</p>
        <Link href="/register/" className={buttonClass("primary", true)}>
          {t("temur.guest.cta")}
        </Link>
      </div>
    </>
  );
}
