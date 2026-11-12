"use client";
import { useT } from "@/lib/i18n";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DailyStat } from "./types";
import { useReducedMotion } from "./useReducedMotion";

const short = (d: string) => d.slice(5);

/** 30-day XP bars; tooltip also shows answered/correct. */
export function XpChart({ daily }: { daily: DailyStat[] }) {
  const t = useT();
  const reduced = useReducedMotion();
  const total = daily.reduce((s, d) => s + d.xp, 0);
  return (
    <section aria-label={t("admin.stats.xpOverTheLast")}>
      <h3 className="mb-1 text-sm">{t("admin.stats.xpLast", { n: daily.length })} <span className="font-semibold text-ink-soft">{t("admin.stats.totalN", { n: total.toLocaleString("en") })}</span></h3>
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
