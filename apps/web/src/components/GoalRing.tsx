"use client";
import { useT } from "@dtmai/i18n";

/** Daily XP goal progress ring. */
export function GoalRing({ done, goal, size = 64 }: { done: number; goal: number; size?: number }) {
  const t = useT();
  const r = (size - 10) / 2;
  const c = 2 * Math.PI * r;
  const pct = goal > 0 ? Math.min(1, done / goal) : 0;
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }} role="img" aria-label={t("goal.label", { done, goal })}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" strokeWidth={8} className="stroke-line" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth={8}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - pct)}
          className={pct >= 1 ? "stroke-gold-deep" : "stroke-green-deep"}
        />
      </svg>
      <span className="absolute text-xs font-extrabold">{Math.round(pct * 100)}%</span>
    </div>
  );
}
