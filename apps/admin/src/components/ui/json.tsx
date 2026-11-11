"use client";
import { useEffect, useState } from "react";
import { Textarea } from "./controls";

/** JSON text editor; reports parse errors inline and only calls onChange with valid JSON. */
export function JsonEditor({ value, onChange, rows = 8, hint }: { value: unknown; onChange: (v: unknown) => void; rows?: number; hint?: string }) {
  const [text, setText] = useState(() => JSON.stringify(value ?? {}, null, 2));
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    setText((t) => {
      try {
        return JSON.stringify(JSON.parse(t)) === JSON.stringify(value ?? {}) ? t : JSON.stringify(value ?? {}, null, 2);
      } catch {
        return JSON.stringify(value ?? {}, null, 2);
      }
    });
  }, [value]);
  return (
    <div>
      <Textarea
        rows={rows}
        spellCheck={false}
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          try {
            onChange(JSON.parse(e.target.value));
            setErr(null);
          } catch (x) {
            setErr((x as Error).message);
          }
        }}
      />
      {err ? <p className="text-[11px] font-bold text-red-deep">{err}</p> : hint && <p className="text-[11px] text-ink-soft">{hint}</p>}
    </div>
  );
}
