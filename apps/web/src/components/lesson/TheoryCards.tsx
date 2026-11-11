"use client";
import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Button, Mascot } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { RichText } from "@/components/RichText";
import type { PathLesson } from "@/lib/api";

export type TheoryCard = NonNullable<PathLesson["theory"]>[number];

/** Full-screen stack of theory cards: dots, CONTINUE, skip. Calls `onDone` after the last card or on skip/close. */
export function TheoryCards({ cards, title, doneLabel, onDone }: { cards: TheoryCard[]; title?: string; doneLabel?: string; onDone: () => void }) {
  const t = useT();
  const reduce = useReducedMotion();
  const [i, setI] = useState(0);
  const [dir, setDir] = useState(1);
  const last = i === cards.length - 1;
  const card = cards[i];

  const go = useCallback(() => {
    if (last) return onDone();
    setDir(1);
    setI((x) => x + 1);
  }, [last, onDone]);
  const back = () => {
    setDir(-1);
    setI((x) => Math.max(0, x - 1));
  };

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key === "Escape") onDone();
      else if (e.key === "Enter" && !(e.target as HTMLElement).closest("button,a")) {
        e.preventDefault();
        go();
      }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [go, onDone]);

  if (!card) return null;
  return (
    <div role="dialog" aria-modal="true" aria-label={title ?? t("theory.title")} className="fixed inset-0 z-50 flex flex-col bg-white">
      <header className="mx-auto flex w-full max-w-3xl items-center gap-4 px-4 py-5">
        <button type="button" aria-label={t("theory.close")} className="text-3xl font-extrabold text-ink-soft" onClick={onDone}>
          ×
        </button>
        <ol className="flex flex-1 justify-center gap-2" aria-label={t("theory.progress", { n: i + 1, total: cards.length })}>
          {cards.map((c, k) => (
            <li key={k} aria-current={k === i ? "step" : undefined} className={`h-2.5 rounded-full transition-all ${k === i ? "w-8 bg-brand" : k < i ? "w-2.5 bg-brand" : "w-2.5 bg-line"}`} />
          ))}
        </ol>
        {!last ? (
          <button type="button" className="text-sm font-extrabold uppercase text-ink-soft" onClick={onDone}>
            {t("theory.skip")}
          </button>
        ) : (
          <span className="w-10" />
        )}
      </header>
      <div className="relative mx-auto w-full max-w-3xl flex-1 overflow-y-auto px-4 pb-6">
        <AnimatePresence mode="wait" initial={false} custom={dir}>
          <motion.article
            key={i}
            custom={dir}
            initial={reduce ? false : { x: dir * 48, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={reduce ? { opacity: 0 } : { x: dir * -48, opacity: 0 }}
            transition={{ duration: reduce ? 0 : 0.22, ease: "easeOut" }}
            className="flex flex-col gap-4"
          >
            <div className="flex items-center gap-3">
              <Mascot mood="thinking" size={72} alt="" className="h-auto w-16 shrink-0" />
              <h1 className="text-2xl">
                <RichText text={card.title} />
              </h1>
            </div>
            <p className="text-lg leading-relaxed">
              <RichText text={card.body_md} />
            </p>
            {card.example_md && (
              <div className="rounded-card border-2 border-line bg-snow p-4">
                <p className="mb-1 text-sm font-extrabold uppercase text-ink-soft">{t("theory.example")}</p>
                <p className="leading-relaxed">
                  <RichText text={card.example_md} />
                </p>
              </div>
            )}
          </motion.article>
        </AnimatePresence>
      </div>
      <footer className="border-t-2 border-line px-4 pt-5 pb-[max(1.25rem,env(safe-area-inset-bottom))]">
        <div className="mx-auto flex max-w-3xl gap-3">
          {i > 0 && (
            <Button variant="secondary" onClick={back}>
              {t("theory.back")}
            </Button>
          )}
          <Button autoFocus block onClick={go}>
            {last ? (doneLabel ?? t("common.continue")) : t("common.continue")}
          </Button>
        </div>
      </footer>
    </div>
  );
}
