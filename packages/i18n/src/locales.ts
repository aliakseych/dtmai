import uzLatn from "./messages/uz-Latn.json";
import uzCyrl from "./messages/uz-Cyrl.json";
import ru from "./messages/ru.json";
import en from "./messages/en.json";

export const LOCALES = ["uz-Latn", "uz-Cyrl", "ru", "en"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "uz-Latn";

export const LOCALE_LABELS: Record<Locale, string> = {
  "uz-Latn": "O‘zbekcha",
  "uz-Cyrl": "Ўзбекча",
  ru: "Русский",
  en: "English",
};

export type MessageKey = keyof typeof uzLatn;
export type Messages = Record<MessageKey, string>;

export const MESSAGES: Record<Locale, Messages> = {
  "uz-Latn": uzLatn,
  "uz-Cyrl": uzCyrl as Messages,
  ru: ru as Messages,
  en: en as Messages,
};

export function isLocale(v: unknown): v is Locale {
  return typeof v === "string" && (LOCALES as readonly string[]).includes(v);
}

export function translate(
  locale: Locale,
  key: MessageKey,
  params?: Record<string, string | number>,
): string {
  const raw = MESSAGES[locale][key] ?? MESSAGES[DEFAULT_LOCALE][key] ?? key;
  if (!params) return raw;
  return raw.replace(/\{(\w+)\}/g, (m, k: string) => (k in params ? String(params[k]) : m));
}
