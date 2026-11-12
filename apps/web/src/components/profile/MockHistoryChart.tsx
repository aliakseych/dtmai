"use client";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useReducedMotion } from "motion/react";
import { useLocale, useT } from "@dtmai/i18n";
import type { Stats } from "./types";
import { shortDate } from "./format";

/** Mock exam score history (% of max), oldest to newest. */
export function MockHistoryChart({ mocks }: { mocks: Stats["mocks"] }) {
  const t = useT();
  const { locale } = useLocale();
  const reduce = useReducedMotion();
  const data = [...mocks].reverse().map((m) => ({
    ...m,
    pct: m.max_score > 0 ? Math.round((m.score / m.max_score) * 100) : 0,
    label: shortDate(m.taken_at.slice(0, 10), locale),
  }));
  return (
    <div role="img" aria-label={t("profile.stats.mocks")} className="h-52 w-full min-w-0">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 12, right: 12, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke="var(--color-line)" />
          <XAxis dataKey="label" tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={24} tick={{ fontSize: 11, fill: "var(--color-ink-soft)" }} />
          <YAxis width={36} domain={[0, 100]} unit="%" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "var(--color-ink-soft)" }} />
          <Tooltip
            content={({ active, payload }) => {
              const p = active ? payload?.[0]?.payload : undefined;
              if (!p) return null;
              return (
                <div className="rounded-xl border-2 border-line bg-white px-3 py-2 text-sm">
                  <div className="font-extrabold text-ink">{p.label}</div>
                  <div className="text-ink-soft">
                    {t("profile.stats.score")}: {p.score}/{p.max_score} ({p.pct}%)
                  </div>
                </div>
              );
            }}
          />
          <Line
            type="monotone"
            dataKey="pct"
            stroke="var(--color-brand)"
            strokeWidth={3}
            dot={{ r: 5, fill: "var(--color-accent)", stroke: "var(--color-brand)", strokeWidth: 2 }}
            activeDot={{ r: 7 }}
            isAnimationActive={!reduce}
            animationDuration={800}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
