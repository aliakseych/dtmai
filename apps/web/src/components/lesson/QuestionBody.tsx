"use client";
import { useEffect, useId, useState } from "react";
import { OptionGroup, OptionTile, type OptionState, Icon } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { RichText } from "@/components/RichText";
import { api, type ItemOut, type Media, type Passage } from "@/lib/api";
import { mediaUrl } from "@/lib/env";

export type Response = Record<string, unknown>;
type Opt = { id: string; text?: string; media?: Media[] };
type Pair = { id: string; text?: string };

const arr = <T,>(v: unknown): T[] => (Array.isArray(v) ? (v as T[]) : []);
const children = (it: ItemOut): ItemOut[] => (it as ItemOut & { children?: ItemOut[] }).children ?? [];
const options = (it: ItemOut) => arr<Opt>(it.payload.options);

/** True when the response is complete enough to submit. */
export function isAnswered(it: ItemOut, v: Response | null): boolean {
  if (!v) return false;
  switch (it.kind) {
    case "single_choice":
      return typeof v.choice === "string";
    case "multi_choice":
      return arr(v.choices).length > 0;
    case "numeric":
      return v.value !== undefined && v.value !== "" && !Number.isNaN(Number(v.value));
    case "short_text":
      return typeof v.text === "string" && v.text.trim() !== "";
    case "matching":
      return Object.keys((v.pairs as object) ?? {}).length === arr(it.payload.left).length;
    case "ordering":
      return arr(v.order).length > 0; // set only after the learner moved an item
    case "passage_group": {
      const a = (v.answers as Record<string, Response>) ?? {};
      const kids = children(it);
      return kids.length > 0 && kids.every((c) => isAnswered(c, a[c.id] ?? null));
    }
    default:
      return false;
  }
}

/** Numeric input: unicode minus, no spaces, a single comma is the decimal mark, several are thousands separators. */
function normalizeNumber(raw: string): string {
  const s = raw.replace(/[\s\u00a0\u202f]/g, "").replace(/[\u2212\u2013]/g, "-");
  const commas = s.split(",").length - 1;
  if (commas === 1 && !s.includes(".")) return s.replace(",", ".");
  return s.replace(/,/g, "");
}

function MediaList({ media }: { media: Media[] }) {
  return (
    <>
      {media.map((m) =>
        m.kind === "image" ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img key={m.url} src={mediaUrl(m.url)} alt={m.alt ?? ""} className="max-h-72 w-auto max-w-full self-center rounded-card border-2 border-line object-contain" />
        ) : (
          <audio key={m.url} src={mediaUrl(m.url)} controls className="w-full" />
        ),
      )}
    </>
  );
}

const passages = new Map<string, Promise<Passage>>();
function usePassage(id: string | null): Passage | null {
  const [p, setP] = useState<Passage | null>(null);
  useEffect(() => {
    if (!id) return setP(null);
    let live = true;
    let req = passages.get(id);
    if (!req) {
      req = api.unwrap(api.client.GET("/v1/bank/passages/{passage_id}", { params: { path: { passage_id: id } } }));
      passages.set(id, req);
    }
    req.then(
      (x) => live && setP(x),
      () => passages.delete(id),
    );
    return () => {
      live = false;
    };
  }, [id]);
  return p;
}

function correctSet(it: ItemOut, correct: Response | null): string[] {
  if (!correct) return [];
  if (it.kind === "single_choice") return typeof correct.choice === "string" ? [correct.choice] : [];
  if (it.kind === "multi_choice") return arr<string>(correct.choices);
  return [];
}

/** Human-readable correct answer for the feedback sheet (ids mapped to option text). */
export function correctText(it: ItemOut, correct: Response | null): string {
  if (!correct) return "";
  const byId = (id: string) => {
    const all = [...options(it), ...arr<Pair>(it.payload.right), ...arr<Pair>(it.payload.items)];
    return all.find((o) => o.id === id)?.text ?? id;
  };
  switch (it.kind) {
    case "single_choice":
    case "multi_choice":
      return correctSet(it, correct).map(byId).join(", ");
    case "numeric":
      return String(correct.value ?? "");
    case "short_text":
      return String(correct.text ?? "");
    case "ordering":
      return arr<string>(correct.order).map(byId).join(" → ");
    case "matching": {
      const left = arr<Pair>(it.payload.left);
      return Object.entries((correct.pairs as Record<string, string>) ?? {})
        .map(([l, r]) => `${left.find((x) => x.id === l)?.text ?? l} — ${byId(r)}`)
        .join("; ");
    }
    default:
      return "";
  }
}

/** Question stem, passage, media and the kind-specific answer control. */
export function QuestionBody({
  item,
  value,
  onChange,
  disabled,
  correct,
  wasCorrect,
  stemAs: Stem = "h1",
}: {
  item: ItemOut;
  value: Response | null;
  onChange: (v: Response) => void;
  disabled?: boolean;
  /** correct_response once checked (lessons) */
  correct?: Response | null;
  wasCorrect?: boolean;
  /** Element for the stem; embedded cards (home daily question) use "p" so the page keeps one h1. */
  stemAs?: "h1" | "p";
}) {
  const t = useT();
  const inputId = useId();
  const passage = usePassage(item.passage_id);
  const checked = correct != null;
  const ok = new Set(correctSet(item, correct ?? null));
  const picked = new Set<string>(item.kind === "single_choice" ? (typeof value?.choice === "string" ? [value.choice] : []) : arr<string>(value?.choices));

  const optState = (id: string): OptionState => {
    if (checked) return ok.has(id) ? "correct" : picked.has(id) ? "incorrect" : "idle";
    return picked.has(id) ? "selected" : "idle";
  };

  // Ordering starts in the default order and only counts as answered after one move.
  const items = arr<Pair>(item.payload.items);
  const moved = arr<string>(value?.order);
  const orderIds = moved.length ? moved : items.map((i) => i.id);

  const body = (() => {
    switch (item.kind) {
      case "single_choice":
      case "multi_choice": {
        const multi = item.kind === "multi_choice";
        return (
          <OptionGroup label={t("lesson.options")} multi={multi} className="flex flex-col gap-3">
            {options(item).map((o, i) => (
              <OptionTile
                key={o.id}
                index={i}
                multi={multi}
                disabled={disabled}
                state={optState(o.id)}
                onSelect={() =>
                  onChange(multi ? { choices: picked.has(o.id) ? [...picked].filter((x) => x !== o.id) : [...picked, o.id] } : { choice: o.id })
                }
              >
                <span className="flex flex-col gap-2">
                  {o.text && <RichText text={o.text} />}
                  {o.media && <MediaList media={o.media} />}
                </span>
              </OptionTile>
            ))}
          </OptionGroup>
        );
      }
      case "numeric":
      case "short_text": {
        const num = item.kind === "numeric";
        const key = num ? "value" : "text";
        return (
          <div className="flex flex-col gap-1">
            <label htmlFor={inputId} className="text-sm font-bold uppercase text-ink-soft">
              {t("lesson.answerLabel")}
              {num && typeof item.payload.unit === "string" ? ` (${item.payload.unit})` : ""}
            </label>
            <input
              id={inputId}
              inputMode={num ? "decimal" : "text"}
              autoComplete="off"
              disabled={disabled}
              value={String(value?.[key] ?? "")}
              onChange={(e) => onChange({ [key]: num ? normalizeNumber(e.target.value) : e.target.value })}
              aria-invalid={checked && !wasCorrect ? true : undefined}
              className="rounded-2xl border-2 border-line bg-snow px-4 py-3 text-lg text-ink focus:border-brand"
            />
          </div>
        );
      }
      case "matching": {
        const left = arr<Pair>(item.payload.left);
        const right = arr<Pair>(item.payload.right);
        const pairs = (value?.pairs as Record<string, string>) ?? {};
        return (
          <ul className="flex flex-col gap-4">
            {left.map((l) => (
              <li key={l.id} className="flex flex-col gap-2">
                <span className="font-bold">
                  <RichText text={l.text ?? ""} />
                </span>
                <div role="radiogroup" aria-label={l.text ?? l.id} className="flex flex-wrap gap-2">
                  {right.map((r) => (
                    <button
                      key={r.id}
                      type="button"
                      role="radio"
                      aria-checked={pairs[l.id] === r.id}
                      disabled={disabled}
                      onClick={() => onChange({ pairs: { ...pairs, [l.id]: r.id } })}
                      className={`rounded-2xl border-2 px-3 py-2 text-left font-bold ${pairs[l.id] === r.id ? "border-brand bg-brand-soft text-brand" : "border-line text-ink"}`}
                    >
                      <RichText text={r.text ?? r.id} />
                    </button>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        );
      }
      case "ordering": {
        const move = (i: number, d: number) => {
          const next = [...orderIds];
          [next[i], next[i + d]] = [next[i + d], next[i]];
          onChange({ order: next });
        };
        return (
          <ol className="flex flex-col gap-2">
            {orderIds.map((id, i) => (
              <li key={id} className="flex items-center gap-2 rounded-2xl border-2 border-line bg-white px-3 py-2">
                <span className="flex-1 font-bold">
                  <RichText text={items.find((x) => x.id === id)?.text ?? id} />
                </span>
                <button type="button" disabled={disabled || i === 0} aria-label={t("lesson.moveUp")} onClick={() => move(i, -1)} className="grid size-11 place-items-center rounded-xl border-2 border-line disabled:opacity-40">
                  <Icon name="arrow-up" size={20} />
                </button>
                <button type="button" disabled={disabled || i === orderIds.length - 1} aria-label={t("lesson.moveDown")} onClick={() => move(i, 1)} className="grid size-11 place-items-center rounded-xl border-2 border-line disabled:opacity-40">
                  <Icon name="arrow-down" size={20} />
                </button>
              </li>
            ))}
          </ol>
        );
      }
      case "passage_group": {
        const answers = (value?.answers as Record<string, Response>) ?? {};
        const right = (correct?.answers as Record<string, Response> | undefined) ?? null;
        return (
          <div className="flex flex-col gap-8">
            {children(item).map((c) => (
              <QuestionBody
                key={c.id}
                item={c}
                value={answers[c.id] ?? null}
                onChange={(v) => onChange({ answers: { ...answers, [c.id]: v } })}
                disabled={disabled}
                correct={right?.[c.id] ?? null}
                wasCorrect={wasCorrect}
              />
            ))}
          </div>
        );
      }
      default:
        return <p className="text-ink-soft">{t("lesson.unsupported")}</p>;
    }
  })();

  return (
    <div className="flex flex-col gap-5">
      {passage && (
        <section aria-label={t("lesson.passage")} className="flex max-h-64 flex-col gap-3 overflow-y-auto rounded-card border-2 border-line bg-snow p-4 font-semibold">
          <RichText text={passage.text} />
          <MediaList media={passage.media} />
        </section>
      )}
      <Stem className="text-2xl font-extrabold">
        <RichText text={item.stem} />
      </Stem>
      <MediaList media={item.media} />
      {body}
    </div>
  );
}
