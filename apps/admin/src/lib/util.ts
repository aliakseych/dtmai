import { ApiError, NetworkError } from "@dtmai/api-client";
import { LOCALES, translate } from "@dtmai/i18n";
import { currentLocale } from "./api";

export const LOCALE_LIST = LOCALES as readonly string[];
export type Names = Record<string, string>;

/** Best display name from a locale map: current locale → uz-Latn → en → ru → anything. */
export function nm(names: Names | undefined | null, fallback = "—"): string {
  if (!names) return fallback;
  const loc = currentLocale();
  return names[loc] || (loc.startsWith("uz") ? names.uz : "") || names["uz-Latn"] || names.uz || names.en || names.ru || Object.values(names).find(Boolean) || fallback;
}

const STATUS_KEY: Record<number, string> = {
  400: "admin.error.badRequest", 401: "admin.error.unauthorized", 403: "admin.error.forbidden", 404: "admin.error.notFound",
  409: "admin.error.conflict", 422: "admin.error.validation", 429: "admin.error.tooMany",
};
/** Localized, user-facing message for any thrown value: problem `code`/status → i18n key, never the raw English detail. */
export function errMsg(e: unknown): string {
  const tr = (k: string): string => translate(currentLocale() as never, k as never);
  if (e instanceof NetworkError) return tr("admin.error.network");
  if (e instanceof ApiError) {
    const byCode = `admin.error.code.${e.code}`;
    const hit = tr(byCode);
    if (hit && hit !== byCode) return hit;
    return tr(STATUS_KEY[e.status] ?? (e.status >= 500 ? "admin.error.server" : "admin.error.generic"));
  }
  return tr("admin.error.generic");
}

/** Per-field messages from a 422 problem (`errors[]`, or legacy pydantic `detail[]`, → `{field: msg}`); empty otherwise. */
export function fieldErrors(e: unknown): Record<string, string> {
  if (e instanceof ApiError && e.status === 409) return { code: translate(currentLocale() as never, "admin.error.field.duplicate_code" as never) };
  if (!(e instanceof ApiError) || e.status !== 422) return {};
  const p = e.problem as { errors?: unknown; detail?: unknown } | undefined;
  const d = Array.isArray(p?.errors) ? p.errors : p?.detail;
  if (typeof d === "string") {
    const m = /^(\w+) /.exec(d);
    return m ? { [m[1]!]: translate(currentLocale() as never, "admin.error.field.invalid" as never) } : {};
  }
  if (!Array.isArray(d)) return {};
  const out: Record<string, string> = {};
  for (const x of d as { loc?: unknown[]; type?: string }[]) {
    const f = String(x.loc?.[x.loc.length - 1] ?? "");
    if (!f || out[f]) continue;
    const key = `admin.error.field.${x.type ?? ""}`;
    const msg = translate(currentLocale() as never, key as never);
    out[f] = msg && msg !== key ? msg : translate(currentLocale() as never, "admin.error.field.invalid" as never);
  }
  return out;
}
/** Thousands grouped with a no-break space for uz/ru ("49 000"); locale default otherwise. */
export const fmtNum = (n: number) => {
  const loc = currentLocale();
  return loc === "en" ? new Intl.NumberFormat("en").format(n) : new Intl.NumberFormat("en").format(n).replace(/,/g, "\u00A0");
};
export const uuid = () => crypto.randomUUID();
export function fmtDate(s?: string | null) {
  return s ? new Intl.DateTimeFormat(currentLocale() === "uz-Cyrl" ? "uz-Cyrl-UZ" : currentLocale(), { dateStyle: "short", timeStyle: "short" }).format(new Date(s)) : "—";
}

export const QUESTION_KINDS = ["single_choice", "multi_choice", "numeric", "short_text", "matching", "ordering", "passage_group"] as const;
export type Kind = (typeof QUESTION_KINDS)[number];
export const QUESTION_STATUSES = ["draft", "auto_agreed", "escalated", "needs_human", "verified", "hidden", "retired"] as const;
export const BLUEPRINT_KINDS = ["official", "generated", "template"] as const;
export const SOURCE_KINDS = ["previous_year", "bluebook", "ai_generated", "harvested", "custom"] as const;
