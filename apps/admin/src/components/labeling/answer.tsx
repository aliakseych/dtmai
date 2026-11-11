"use client";
import { Md } from "@/components/ui/markdown";

type R = Record<string, unknown>;
export interface Opt { id: string; text?: string }
export const optsOf = (payload: R, key = "options"): Opt[] => (Array.isArray(payload[key]) ? (payload[key] as Opt[]) : []);
export const letter = (i: number) => String.fromCharCode(65 + i);

/** Human text of an answer for the given question kind. */
export function fmtAnswer(kind: string, payload: R, a: R | null | undefined): string {
  if (!a) return "—";
  const label = (key: string, id: string) => {
    const list = optsOf(payload, key);
    const i = list.findIndex((o) => o.id === id);
    return i >= 0 ? `${letter(i)}` : id;
  };
  switch (kind) {
    case "single_choice": return label("options", String(a.choice));
    case "multi_choice": return (Array.isArray(a.choices) ? a.choices : []).map((c) => label("options", String(c))).join(", ") || "—";
    case "numeric": return `${a.value}${a.tolerance ? ` ± ${a.tolerance}` : ""}`;
    case "short_text": return (Array.isArray(a.accepted) ? a.accepted : []).join(" | ");
    case "matching": return Object.entries((a.pairs as Record<string, string>) ?? {}).map(([l, r]) => `${l}→${r}`).join(", ");
    case "ordering": return (Array.isArray(a.order) ? a.order : []).join(" › ");
    default: return JSON.stringify(a);
  }
}

export function QuestionBody({ kind, payload, picked, suggested, onPick }: { kind: string; payload: R; picked: string[]; suggested: string[]; onPick: (id: string) => void }) {
  if (kind === "single_choice" || kind === "multi_choice") {
    return (
      <ul className="space-y-2">
        {optsOf(payload).map((o, i) => {
          const on = picked.includes(o.id), sug = suggested.includes(o.id);
          return (
            <li key={o.id}>
              <button type="button" onClick={() => onPick(o.id)} aria-pressed={on}
                className={`flex w-full items-start gap-3 rounded-xl border-2 p-3 text-left ${on ? "border-blue bg-blue-soft" : "border-line bg-white hover:bg-snow"} ${sug ? "ring-2 ring-green" : ""}`}>
                <kbd className="grid h-7 w-7 shrink-0 place-items-center rounded-md border border-line bg-snow text-sm font-extrabold">{letter(i)}</kbd>
                <span className="min-w-0 flex-1"><Md text={o.text ?? ""} /></span>
                {sug && <span className="text-xs font-extrabold text-green-deep">model</span>}
              </button>
            </li>
          );
        })}
      </ul>
    );
  }
  if (kind === "matching") {
    return <div className="grid grid-cols-2 gap-4 text-sm"><ol className="space-y-1">{optsOf(payload, "left").map((o) => <li key={o.id}><code>{o.id}</code> <Md text={o.text ?? ""} /></li>)}</ol><ol className="space-y-1">{optsOf(payload, "right").map((o) => <li key={o.id}><code>{o.id}</code> <Md text={o.text ?? ""} /></li>)}</ol></div>;
  }
  if (kind === "ordering") {
    return <ul className="space-y-1 text-sm">{optsOf(payload, "items").map((o) => <li key={o.id}><code>{o.id}</code> <Md text={o.text ?? ""} /></li>)}</ul>;
  }
  return null;
}
