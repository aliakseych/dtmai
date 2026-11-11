"use client";
import { motion, useReducedMotion } from "motion/react";
import { useT } from "@dtmai/i18n";

/** Animated accuracy donut (0..1). */
export function AccuracyRing({ value, size = 48 }: { value: number; size?: number }) {
  const t = useT();
  const reduce = useReducedMotion();
  const pct = Math.max(0, Math.min(1, value));
  const r = (size - 8) / 2;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }} role="img" aria-label={`${t("profile.stats.accuracy")}: ${Math.round(pct * 100)}%`}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden="true">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" strokeWidth={6} className="stroke-line" />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth={6}
          strokeLinecap="round"
          strokeDasharray={c}
          className="stroke-brand"
          initial={{ strokeDashoffset: reduce ? c * (1 - pct) : c }}
          animate={{ strokeDashoffset: c * (1 - pct) }}
          transition={{ duration: reduce ? 0 : 0.9, ease: "easeOut" }}
        />
      </svg>
    </div>
  );
}
