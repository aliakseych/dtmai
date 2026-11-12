"use client";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useReducedMotion } from "motion/react";
import { useLocale, useT } from "@dtmai/i18n";
import type { Stats } from "./types";
import { dayLabel, shortDate } from "./format";

/** 30-day XP bar chart; today's bar is highlighted in the accent colour. */
export function ActivityBars({ daily }: { daily: Stats["daily"] }) {
  const t = useT();
  const { locale } = useLocale();
  const reduce = useReducedMotion();
  const data = daily.map((d) => ({ ...d, label: dayLabel(d.date) }));
  const total = daily.reduce((s, d) => s + d.xp, 0);
  return (
    <div role="img" aria-label={`${t("profile.stats.activity")}: ${total} ${t("stat.xp")}`} className="h-52 w-full min-w-0">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 4, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke="var(--color-line)" />
          <XAxis dataKey="label" tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={16} tick={{ fontSize: 11, fill: "var(--color-ink-soft)" }} />
          <YAxis width={32} tickLine={false} axisLine={false} allowDecimals={false} tick={{ fontSize: 11, fill: "var(--color-ink-soft)" }} />
          <Tooltip
            cursor={{ fill: "var(--color-snow)" }}
            content={({ active, payload }) => {
              const p = active ? payload?.[0]?.payload : undefined;
              if (!p) return null;
              return (
                <div className="rounded-xl border-2 border-line bg-white px-3 py-2 text-sm">
                  <div className="font-extrabold text-ink">{shortDate(p.date, locale)}</div>
                  <div className="text-ink-soft">{t("profile.stats.dayTip", { xp: p.xp, correct: p.correct, answered: p.answered })}</div>
                </div>
              );
            }}
          />
          <Bar dataKey="xp" radius={[6, 6, 0, 0]} isAnimationActive={!reduce} animationDuration={700}>
            {data.map((d, i) => (
              <Cell key={d.date} fill={i === data.length - 1 ? "var(--color-accent)" : "var(--color-brand)"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
