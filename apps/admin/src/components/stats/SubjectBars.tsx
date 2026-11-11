"use client";
import type { SubjectStat } from "./types";

/** Mastery (0..1) per subject as flat progress bars; unknown mastery renders an empty bar. */
export function SubjectBars({ rows, subjectName }: { rows: SubjectStat[]; subjectName: (id: string) => string }) {
  return (
    <section aria-label="Mastery by subject">
      <h3 className="mb-1 text-sm">Mastery by subject</h3>
      {rows.length === 0 ? <p className="text-xs text-ink-soft">No answers yet.</p> : (
        <ul className="max-h-56 space-y-2 overflow-y-auto rounded-xl border-2 border-line bg-white p-3">
          {rows.map((r) => {
            const pct = r.mastery == null ? 0 : Math.round(r.mastery * 100);
            return (
              <li key={r.subject_id}>
                <div className="flex justify-between text-xs"><span className="font-extrabold">{subjectName(r.subject_id)}</span><span className="tabular-nums text-ink-soft">{r.mastery == null ? "—" : `${pct}%`} · {r.correct}/{r.answered}</span></div>
                <div role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} className="mt-0.5 h-3 overflow-hidden rounded-full bg-snow">
                  <div className="h-full rounded-full bg-brand" style={{ width: `${pct}%` }} />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
