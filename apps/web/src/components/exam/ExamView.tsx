"use client";
import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { PageTitle } from "@/components/PageTitle";
import { RichText } from "@/components/RichText";
import { listFaq, type Faq } from "@/lib/planner";
import { useAsync } from "@/lib/useAsync";

/** `/exam`: admin-edited exam rules and FAQ as an accordion. */
export function ExamView() {
  const t = useT();
  const { locale } = useLocale();
  const { state, reload } = useAsync(() => listFaq(locale), [locale]);
  return (
    <>
      <PageTitle>{t("exam.title")}</PageTitle>
      <p className="mb-4 text-ink-soft">{t("exam.intro")}</p>
      <AsyncView state={state} onRetry={reload} isEmpty={(d) => d.length === 0} emptyText={t("exam.empty")}>
        {(items) => (
          <ul className="flex flex-col gap-2">
            {items.map((f) => (
              <Item key={f.id} faq={f} />
            ))}
          </ul>
        )}
      </AsyncView>
    </>
  );
}

function Item({ faq }: { faq: Faq }) {
  const t = useT();
  const reduce = useReducedMotion();
  const [open, setOpen] = useState(false);
  const panel = `faq-${faq.id}`;
  return (
    <li className="rounded-card border-2 border-line bg-white">
      <h2 className="text-base">
        <button type="button" aria-expanded={open} aria-controls={panel} onClick={() => setOpen(!open)} className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left font-extrabold">
          <span className="min-w-0 break-words">{faq.question}</span>
          <motion.span aria-hidden animate={{ rotate: open ? 180 : 0 }} transition={reduce ? { duration: 0 } : { type: "spring", stiffness: 400, damping: 25 }} className="shrink-0">
            ▾
          </motion.span>
        </button>
      </h2>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            id={panel}
            initial={reduce ? false : { height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={reduce ? { opacity: 0 } : { height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="flex flex-col gap-2 px-4 pb-4">
              {faq.answer.split(/\n{2,}/).map((para, i) => (
                <p key={i}>
                  <RichText text={para} />
                </p>
              ))}
              {!faq.verified && <p className="text-sm font-bold text-ink-soft">{t("plan.unverified")}</p>}
              {faq.source_url && (
                <a href={faq.source_url} target="_blank" rel="noopener noreferrer" className="text-sm font-extrabold text-blue-deep underline">
                  {t("exam.source")}
                </a>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </li>
  );
}
