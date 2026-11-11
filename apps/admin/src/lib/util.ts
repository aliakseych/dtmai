import { LOCALES } from "@dtmai/i18n";

export const LOCALE_LIST = LOCALES as readonly string[];
export type Names = Record<string, string>;

/** Best display name from a locale map: en → ru → uz-Latn → anything. */
export function nm(names: Names | undefined | null, fallback = "—"): string {
  if (!names) return fallback;
  return names.en || names.ru || names["uz-Latn"] || Object.values(names).find(Boolean) || fallback;
}
export const errMsg = (e: unknown) => (e instanceof Error ? e.message : String(e));
export const uuid = () => crypto.randomUUID();
export function fmtDate(s?: string | null) {
  return s ? new Date(s).toLocaleString("en-GB", { dateStyle: "short", timeStyle: "short" }) : "—";
}

export const QUESTION_KINDS = ["single_choice", "multi_choice", "numeric", "short_text", "matching", "ordering", "passage_group"] as const;
export type Kind = (typeof QUESTION_KINDS)[number];
export const QUESTION_STATUSES = ["draft", "auto_agreed", "escalated", "needs_human", "verified", "hidden", "retired"] as const;
export const BLUEPRINT_KINDS = ["official", "generated", "template"] as const;
export const SOURCE_KINDS = ["previous_year", "bluebook", "ai_generated", "harvested", "custom"] as const;
