"use client";
import { useEffect, type ReactNode } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Button, Icon, Mascot, ProgressBar, type MascotMood } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";

/** One question per screen: progress bar, mascot with speech bubble, content, footer actions. */
export function OnboardingFrame({
  stepKey,
  step,
  total,
  speech,
  mood = "thinking",
  onBack,
  onContinue,
  canContinue,
  continueLabel,
  children,
}: {
  stepKey: string;
  step: number;
  total: number;
  speech: string;
  mood?: MascotMood;
  onBack?: () => void;
  onContinue: () => void;
  canContinue: boolean;
  continueLabel?: string;
  children: ReactNode;
}) {
  const t = useT();
  const reduce = useReducedMotion();
  const label = t("onb.step", { n: step, total });
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [stepKey]);
  useEffect(() => {
    document.title = `${speech} · ${t("app.name")}`;
  }, [speech, t]);
  return (
    <div className="mx-auto flex min-h-dvh max-w-xl flex-col gap-5 px-4 py-6">
      <div className="flex items-center gap-3">
        {onBack ? (
          <button type="button" onClick={onBack} aria-label={t("common.back")} className="grid size-11 shrink-0 place-items-center rounded-xl text-ink-soft hover:bg-snow">
            <Icon name="arrow-left" />
          </button>
        ) : null}
        <ProgressBar value={step} max={total} label={label} />
      </div>
      <AnimatePresence mode="wait">
        <motion.div
          key={stepKey}
          initial={reduce ? false : { opacity: 0, x: 24 }}
          animate={{ opacity: 1, x: 0 }}
          exit={reduce ? { opacity: 0 } : { opacity: 0, x: -24 }}
          transition={{ duration: reduce ? 0 : 0.18 }}
          className="flex flex-1 flex-col gap-5"
        >
          <div className="flex items-center gap-3">
            <Mascot mood={mood} size={96} alt={t("mascot.alt")} className="h-auto w-20 shrink-0" />
            <h1 className="relative rounded-2xl border-2 border-line bg-white px-4 py-3 text-base font-extrabold">
              <span aria-hidden className="absolute -left-2 top-6 size-3 rotate-45 border-b-2 border-l-2 border-line bg-white" />
              {speech}
            </h1>
          </div>
          <div className="flex flex-1 flex-col gap-3">{children}</div>
        </motion.div>
      </AnimatePresence>
      <Button block disabled={!canContinue} onClick={onContinue}>
        {continueLabel ?? t("common.continue")}
      </Button>
    </div>
  );
}
