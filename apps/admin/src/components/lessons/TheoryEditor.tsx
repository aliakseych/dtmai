"use client";
import { Btn, Field, Input, Textarea } from "@/components/ui/controls";
import { Md } from "@/components/ui/markdown";
import type { LessonIn } from "@/lib/catalog";

export type TheoryCard = NonNullable<LessonIn["theory"]>[number];
export const MAX_THEORY_CARDS = 12;

/** Ordered theory cards shown before a lesson's practice. Markdown + $LaTeX$ with live preview. */
export function TheoryEditor({ value, onChange }: { value: TheoryCard[]; onChange: (v: TheoryCard[]) => void }) {
  const patch = (i: number, p: Partial<TheoryCard>) => onChange(value.map((c, j) => (j === i ? { ...c, ...p } : c)));
  const move = (i: number, d: -1 | 1) => {
    const next = [...value];
    [next[i], next[i + d]] = [next[i + d], next[i]];
    onChange(next);
  };
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-extrabold uppercase text-ink-soft">Theory cards ({value.length}/{MAX_THEORY_CARDS})</span>
        <Btn disabled={value.length >= MAX_THEORY_CARDS} onClick={() => onChange([...value, { title: "", body_md: "", example_md: null }])}>Add card</Btn>
      </div>
      {value.map((c, i) => (
        <div key={i} className="space-y-2 rounded-lg border border-line bg-white p-3">
          <div className="flex items-center gap-2">
            <Input className="flex-1" placeholder="Card title" value={c.title} onChange={(e) => patch(i, { title: e.target.value })} />
            <Btn disabled={i === 0} onClick={() => move(i, -1)} aria-label="Move up">↑</Btn>
            <Btn disabled={i === value.length - 1} onClick={() => move(i, 1)} aria-label="Move down">↓</Btn>
            <Btn variant="danger" onClick={() => onChange(value.filter((_, j) => j !== i))} aria-label="Remove card">✕</Btn>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Field label="Body (Markdown + $LaTeX$)"><Textarea rows={6} value={c.body_md} onChange={(e) => patch(i, { body_md: e.target.value })} /></Field>
            <div className="rounded border border-line bg-snow p-2"><div className="mb-1 text-[10px] font-extrabold uppercase text-ink-soft">Preview</div><Md text={c.body_md || "…"} /></div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Field label="Example (optional)"><Textarea rows={4} value={c.example_md ?? ""} onChange={(e) => patch(i, { example_md: e.target.value || null })} /></Field>
            <div className="rounded border border-line bg-snow p-2"><div className="mb-1 text-[10px] font-extrabold uppercase text-ink-soft">Preview</div><Md text={c.example_md || "…"} /></div>
          </div>
        </div>
      ))}
    </div>
  );
}
