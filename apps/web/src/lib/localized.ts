import type { Locale } from "@dtmai/i18n";
import type { Names } from "./api";

/** API content language (`uz`/`ru`/`en`) for a UI locale; both Uzbek scripts map to `uz`. */
export const contentLang = (l: Locale): "uz" | "ru" | "en" => (l === "ru" ? "ru" : l === "en" ? "en" : "uz");

/** Localized name with fallback chain; catalog keys by UI locale (`uz-Latn`), lyceums by content lang (`uz`). */
export function pick(names: Names | undefined | null, l: Locale): string {
  if (!names) return "";
  const n = names as Record<string, string | undefined>;
  return n[l] || n[contentLang(l)] || n["uz-Latn"] || n.uz || n.ru || n.en || "";
}

/** Number/currency formatting follows the UI locale (uz-Cyrl uses the uz-Cyrl BCP-47 tag). */
export const fmt = (l: Locale) => new Intl.NumberFormat(l === "uz-Latn" ? "uz-Latn-UZ" : l === "uz-Cyrl" ? "uz-Cyrl-UZ" : l);
