"use client";
import { Input } from "@/components/ui/controls";
import { Md } from "@/components/ui/markdown";
import { optsOf } from "./answer";

type R = Record<string, unknown>;
/** Free-text drafts per kind: numeric {value,tolerance}; short_text {text}; matching {<leftId>: rightId}; ordering {text}. */
export type Draft = Record<string, string>;

export const TYPED_KINDS = ["numeric", "short_text", "matching", "ordering"] as const;
export const isTyped = (kind: string) => (TYPED_KINDS as readonly string[]).includes(kind);

const splitIds = (s: string) => s.split(/[\s,›>]+/).map((x) => x.trim()).filter(Boolean);
const strs = (v: unknown): string[] => (Array.isArray(v) ? v.map(String) : []);

export function draftFromAnswer(kind: string, a: R | null | undefined): Draft {
  if (!a) return {};
  switch (kind) {
    case "numeric": return { value: a.value != null ? String(a.value) : "", tolerance: a.tolerance ? String(a.tolerance) : "" };
    case "short_text": return { text: strs(a.accepted).join(" | ") };
    case "matching": return Object.fromEntries(Object.entries((a.pairs as Record<string, string>) ?? {}).map(([l, r]) => [l, String(r)]));
    case "ordering": return { text: strs(a.order).join(" ") };
    default: return {};
  }
}

/** Builds the response for a typed kind, or null when the draft is incomplete/invalid. */
export function answerFromDraft(kind: string, payload: R, d: Draft): R | null {
  switch (kind) {
    case "numeric": {
      const raw = (d.value ?? "").trim().replace(",", ".");
      if (!raw || !Number.isFinite(Number(raw))) return null;
      const tol = (d.tolerance ?? "").trim().replace(",", ".");
      if (tol && (!Number.isFinite(Number(tol)) || Number(tol) < 0)) return null;
      return tol && Number(tol) > 0 ? { value: Number(raw), tolerance: Number(tol) } : { value: Number(raw) };
    }
    case "short_text": {
      const accepted = (d.text ?? "").split("|").map((x) => x.trim()).filter(Boolean);
      return accepted.length ? { accepted } : null;
    }
    case "matching": {
      const rights = optsOf(payload, "right").map((o) => o.id);
      const pairs: Record<string, string> = {};
      for (const l of optsOf(payload, "left")) {
        const v = (d[l.id] ?? "").trim();
        const r = rights.find((x) => x.toLowerCase() === v.toLowerCase());
        if (!r) return null;
        pairs[l.id] = r;
      }
      return Object.keys(pairs).length ? { pairs } : null;
    }
    case "ordering": {
      const ids = optsOf(payload, "items").map((o) => o.id);
      const got = splitIds(d.text ?? "").map((x) => ids.find((i) => i.toLowerCase() === x.toLowerCase()));
      if (got.length !== ids.length || got.some((x) => !x) || new Set(got).size !== ids.length) return null;
      return { order: got as string[] };
    }
    default: return null;
  }
}

/** Semantic equality of two responses of the same kind (used to decide accept vs edit). */
export function sameAnswer(kind: string, a: R | null | undefined, b: R | null | undefined): boolean {
  if (!a || !b) return false;
  switch (kind) {
    case "single_choice": return String(a.choice) === String(b.choice);
    case "multi_choice": { const x = strs(a.choices).sort(), y = strs(b.choices).sort(); return x.length === y.length && x.every((v, i) => v === y[i]); }
    case "numeric": return Number(a.value) === Number(b.value) && Number(a.tolerance ?? 0) === Number(b.tolerance ?? 0);
    case "short_text": { const x = strs(a.accepted).map((s) => s.trim()).sort(), y = strs(b.accepted).map((s) => s.trim()).sort(); return x.length === y.length && x.every((v, i) => v === y[i]); }
    case "matching": {
      const x = (a.pairs as Record<string, string>) ?? {}, y = (b.pairs as Record<string, string>) ?? {};
      const kx = Object.keys(x);
      return kx.length === Object.keys(y).length && kx.every((k) => x[k] === y[k]);
    }
    case "ordering": { const x = strs(a.order), y = strs(b.order); return x.length === y.length && x.every((v, i) => v === y[i]); }
    default: return JSON.stringify(a) === JSON.stringify(b);
  }
}

/**
 * Typed answer inputs. Inputs carry data-answer="req|opt": Cockpit uses it to move to the next empty
 * required input on Enter and to confirm when all are filled. The first input autofocuses on mount (parent keys by question id).
 */
export function TypedInput({ kind, payload, draft, onChange }: { kind: string; payload: R; draft: Draft; onChange: (d: Draft) => void }) {
  const set = (k: string, v: string) => onChange({ ...draft, [k]: v });
  const label = "text-xs font-extrabold uppercase text-ink-soft";
  if (kind === "numeric") {
    return (
      <div className="flex gap-3">
        <label className="flex-1 space-y-1"><span className={label}>Value</span><Input autoFocus data-answer="req" inputMode="decimal" value={draft.value ?? ""} onChange={(e) => set("value", e.target.value)} /></label>
        <label className="w-40 space-y-1"><span className={label}>± tolerance</span><Input data-answer="opt" inputMode="decimal" value={draft.tolerance ?? ""} onChange={(e) => set("tolerance", e.target.value)} /></label>
      </div>
    );
  }
  if (kind === "short_text") {
    return <label className="block space-y-1"><span className={label}>Accepted answers — separate variants with |</span><Input autoFocus data-answer="req" value={draft.text ?? ""} onChange={(e) => set("text", e.target.value)} /></label>;
  }
  if (kind === "matching") {
    const left = optsOf(payload, "left");
    return (
      <div className="space-y-2">
        <span className={label}>Type the right-hand id for each left item — Enter moves on</span>
        {left.map((l, i) => (
          <label key={l.id} className="flex items-center gap-3">
            <code className="w-8">{l.id}</code>
            <span className="min-w-0 flex-1 text-sm"><Md text={l.text ?? ""} /></span>
            <Input autoFocus={i === 0} data-answer="req" className="w-24" value={draft[l.id] ?? ""} onChange={(e) => set(l.id, e.target.value)} />
          </label>
        ))}
      </div>
    );
  }
  if (kind === "ordering") {
    return <label className="block space-y-1"><span className={label}>Correct order — item ids separated by space or comma</span><Input autoFocus data-answer="req" value={draft.text ?? ""} onChange={(e) => set("text", e.target.value)} /></label>;
  }
  return null;
}
