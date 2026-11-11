"use client";
import { useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { CheckIcon, cn, LockIcon, StarIcon } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import type { UnitStyle } from "./unitStyle";

export type StepState = "completed" | "current" | "open" | "locked";

const R = 44;
const C = 2 * Math.PI * R;

/** One node of the vertical path: completed, current (START bubble, progress ring, pulse) or locked (tooltip). */
export function PathStep({ state, label, title, progress, legendary, style, popped, onOpen }: { state: StepState; label: string; title: string; progress: number; legendary: boolean; style: UnitStyle; popped: boolean; onOpen: () => void }) {
  const t = useT();
  const reduce = useReducedMotion();
  const [tip, setTip] = useState(false);
  const locked = state === "locked";
  const Icon = locked ? LockIcon : state === "completed" ? CheckIcon : StarIcon;
  const face = locked ? "bg-line text-[#afafaf] border-[#cfcfcf]" : state === "completed" ? "bg-gold text-ink border-gold-deep" : style.node;

  return (
    <div className="relative grid h-24 w-24 place-items-center" onMouseLeave={() => setTip(false)}>
      {state === "current" && (
        <>
          <motion.span
            aria-hidden
            className="absolute inset-1 rounded-full border-4 border-brand/40"
            animate={reduce ? undefined : { scale: [1, 1.18], opacity: [0.7, 0] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: "easeOut" }}
          />
          <svg aria-hidden viewBox="0 0 100 100" className="absolute inset-0 -rotate-90">
            <circle cx="50" cy="50" r={R} fill="none" stroke="#e5e5e5" strokeWidth="6" />
            <circle cx="50" cy="50" r={R} fill="none" stroke={style.ring} strokeWidth="6" strokeLinecap="round" strokeDasharray={C} strokeDashoffset={C * (1 - Math.min(1, Math.max(0.04, progress)))} />
          </svg>
          <motion.span
            aria-hidden
            className="absolute -top-7 z-10 rounded-xl border-2 border-line bg-white px-3 py-1 text-sm font-extrabold uppercase text-brand shadow-sm after:absolute after:left-1/2 after:top-full after:-ml-1.5 after:border-x-[6px] after:border-t-[6px] after:border-x-transparent after:border-t-white"
            animate={reduce ? undefined : { y: [0, -6, 0] }}
            transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
          >
            {t("learn.node.start")}
          </motion.span>
        </>
      )}
      <motion.button
        type="button"
        aria-label={label}
        aria-disabled={locked || undefined}
        title={locked ? undefined : title}
        onClick={() => (locked ? setTip((x) => !x) : onOpen())}
        onFocus={() => locked && setTip(true)}
        onBlur={() => setTip(false)}
        onMouseEnter={() => locked && setTip(true)}
        initial={popped && !reduce ? { scale: 0.5 } : false}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 380, damping: 14 }}
        whileTap={locked ? undefined : { y: 4 }}
        className={cn("relative grid h-[72px] w-[72px] place-items-center border-b-8", legendary ? "rounded-2xl" : "rounded-full", face, locked && "cursor-not-allowed")}
      >
        <Icon width={32} height={32} />
      </motion.button>
      {locked && tip && (
        <span role="tooltip" className="pop-in absolute -bottom-3 z-20 w-44 -translate-y-0 rounded-xl border-2 border-line bg-white p-2 text-center text-sm font-bold text-ink-soft shadow-md">
          {t("learn.node.lockedHint")}
        </span>
      )}
    </div>
  );
}
