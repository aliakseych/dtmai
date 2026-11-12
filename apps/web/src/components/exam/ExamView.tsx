"use client";
import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Icon } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { formatDay } from "@/lib/planDates";
import { PageTitle } from "@/components/PageTitle";
import { RichText } from "@/components/RichText";
import { pick } from "@/lib/localized";
import { listEvents, listFaq, type ExamEvent, type Faq } from "@/lib/planner";
import { useAsync } from "@/lib/useAsync";

/** `/exam`: admin-edited exam rules and FAQ as an accordion. */
export function ExamView() {
  const t = useT();
  const { locale } = useLocale();
  const { state, reload } = useAsync(() => listFaq(locale), [locale]);
  const events = useAsync(() => listEvents(), []);
  return (
    <>
      <PageTitle>{t("exam.title")}</PageTitle>
      <p className="mb-4 text-ink-soft">{t("exam.intro")}</p>
      {events.state.status === "ready" && events.state.data.length > 0 && (
        <section aria-label={t("exam.dates")} className="mb-5 flex flex-col gap-2">
          <h2 className="text-lg">{t("exam.dates")}</h2>
          <ul className="flex flex-col gap-2">
            {events.state.data.map((e) => (
              <EventRow key={e.id} e={e} />
            ))}
          </ul>
        </section>
      )}
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
            <Icon name="chevron-down" size={24} />
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
              {faq.source_url && /^https?:\/\//i.test(faq.source_url) && (
                <a href={faq.source_url} target="_blank" rel="noopener noreferrer" className="text-sm font-extrabold text-brand underline">
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

function EventRow({ e }: { e: ExamEvent }) {
  const t = useT();
  const { locale } = useLocale();
  const opts: Intl.DateTimeFormatOptions = { day: "numeric", month: "long", year: "numeric" };
  return (
    <li className="flex flex-wrap items-center justify-between gap-2 rounded-xl border-2 border-line bg-white px-3 py-2">
      <span className="min-w-0 break-words font-extrabold">{pick(e.label, locale)}</span>
      <span className="flex flex-wrap items-center gap-2 text-sm font-bold">
        <span>
          {formatDay(e.starts_on, locale, opts)}
          {e.ends_on && e.ends_on !== e.starts_on ? ` – ${formatDay(e.ends_on, locale, opts)}` : ""}
        </span>
        {!e.verified && <span className="rounded-lg bg-snow px-2 py-0.5 text-ink-soft">{t("exam.approximate")}</span>}
      </span>
    </li>
  );
}
