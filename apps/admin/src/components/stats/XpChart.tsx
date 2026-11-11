"use client";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DailyStat } from "./types";
import { useReducedMotion } from "./useReducedMotion";

const short = (d: string) => d.slice(5);

/** 30-day XP bars; tooltip also shows answered/correct. */
export function XpChart({ daily }: { daily: DailyStat[] }) {
  const reduced = useReducedMotion();
  const total = daily.reduce((s, d) => s + d.xp, 0);
  return (
    <section aria-label="XP over the last 30 days">
      <h3 className="mb-1 text-sm">XP, last {daily.length} days <span className="font-semibold text-ink-soft">· {total.toLocaleString("en")} total</span></h3>
      <div className="h-48 w-full rounded-xl border-2 border-line bg-white p-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={daily} margin={{ top: 4, right: 4, bottom: 0, left: -16 }}>
            <CartesianGrid vertical={false} stroke="var(--color-line)" />
            <XAxis dataKey="date" tickFormatter={short} tick={{ fontSize: 10 }} interval="preserveStartEnd" minTickGap={24} tickLine={false} axisLine={false} />
            <YAxis tick={{ fontSize: 10 }} allowDecimals={false} tickLine={false} axisLine={false} />
            <Tooltip
              cursor={{ fill: "var(--color-brand-soft)" }}
              formatter={(v, _n, p) => [`${v} XP · ${p.payload.correct}/${p.payload.answered} correct`, ""]}
              separator=""
            />
            <Bar dataKey="xp" fill="var(--color-brand)" radius={[4, 4, 0, 0]} isAnimationActive={!reduced} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
