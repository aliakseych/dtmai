"use client";
import type { ReactNode } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Button, Mascot, ProgressBar, type MascotMood } from "@dtmai/ui";
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
  const label = t("onb.step", { n: step, total });
  return (
    <div className="mx-auto flex min-h-dvh max-w-xl flex-col gap-5 px-4 py-6">
      <div className="flex items-center gap-3">
        {onBack ? (
          <button type="button" onClick={onBack} aria-label={t("common.back")} className="text-2xl font-extrabold text-ink-soft">
            ←
          </button>
        ) : null}
        <ProgressBar value={step} max={total} label={label} />
      </div>
      <AnimatePresence mode="wait">
        <motion.div
          key={stepKey}
          initial={{ opacity: 0, x: 24 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -24 }}
          transition={{ duration: 0.18 }}
          className="flex flex-1 flex-col gap-5"
        >
          <div className="flex items-center gap-3">
            <Mascot mood={mood} size={96} alt={t("mascot.alt")} className="h-auto w-20 shrink-0" />
            <div className="relative rounded-2xl border-2 border-line bg-white px-4 py-3 font-extrabold" role="status">
              <span aria-hidden className="absolute -left-2 top-6 size-3 rotate-45 border-b-2 border-l-2 border-line bg-white" />
              {speech}
            </div>
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
