"use client";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { MockStat } from "./types";
import { useReducedMotion } from "./useReducedMotion";

const day = (s: string) => new Date(s).toLocaleDateString("en-GB", { day: "2-digit", month: "short" });

/** Mock score trend (oldest → newest) plus a scrollable list, newest first. */
export function MockHistory({ mocks }: { mocks: MockStat[] }) {
  const reduced = useReducedMotion();
  const data = [...mocks].reverse().map((m) => ({ at: day(m.taken_at), score: m.score, max: m.max_score }));
  return (
    <section aria-label="Mock history">
      <h3 className="mb-1 text-sm">Mock exams</h3>
      {mocks.length === 0 ? <p className="text-xs text-ink-soft">No mocks submitted yet.</p> : (
        <div className="space-y-2">
          {mocks.length > 1 && (
            <div className="h-36 rounded-xl border-2 border-line bg-white p-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
                  <CartesianGrid vertical={false} stroke="var(--color-line)" />
                  <XAxis dataKey="at" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                  <Tooltip formatter={(v, _n, p) => [`${v} / ${p.payload.max}`, "Score"]} />
                  <Line type="monotone" dataKey="score" stroke="var(--color-brand)" strokeWidth={3} dot={{ r: 3, fill: "var(--color-accent)", stroke: "var(--color-brand)" }} isAnimationActive={!reduced} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          <ul className="max-h-48 divide-y divide-line overflow-y-auto rounded-xl border-2 border-line bg-white text-xs">
            {mocks.map((m) => (
              <li key={m.mock_id} className="flex items-center justify-between gap-2 px-3 py-1.5">
                <span className="text-ink-soft">{new Date(m.taken_at).toLocaleString("en-GB", { dateStyle: "short", timeStyle: "short" })}</span>
                <span className="font-extrabold tabular-nums">{m.score} / {m.max_score}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
