import type { Locale } from "@dtmai/i18n";

/** Pure calendar/wizard helpers (local dates, ISO yyyy-mm-dd); no React, no I/O. */
const pad = (n: number) => String(n).padStart(2, "0");
export const toISO = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
export const fromISO = (s: string) => {
  const [y, m, d] = s.split("-").map(Number);
  return new Date(y!, m! - 1, d!, 12);
};
export const addDays = (iso: string, n: number) => {
  const d = fromISO(iso);
  d.setDate(d.getDate() + n);
  return toISO(d);
};
const TASHKENT_DAY = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tashkent", year: "numeric", month: "2-digit", day: "2-digit" });
/** Today's date in Tashkent (the product's day boundary), regardless of the device time zone. */
export const todayISO = () => {
  const p = Object.fromEntries(TASHKENT_DAY.formatToParts(new Date()).map((x) => [x.type, x.value]));
  return `${p.year}-${p.month}-${p.day}`;
};
export const daysBetween = (a: string, b: string) => Math.round((fromISO(b).getTime() - fromISO(a).getTime()) / 86_400_000);
/** Monday-based weekday: 0 = Mon … 6 = Sun (matches the API `available_weekdays`). */
export const weekdayOf = (iso: string) => (fromISO(iso).getDay() + 6) % 7;
export const startOfWeek = (iso: string) => addDays(iso, -weekdayOf(iso));
export const intlTag = (l: Locale) => (l === "uz-Latn" ? "uz-Latn-UZ" : l === "uz-Cyrl" ? "uz-Cyrl-UZ" : l);
const isUz = (l: Locale): l is "uz-Latn" | "uz-Cyrl" => l === "uz-Latn" || l === "uz-Cyrl";
// Browser ICU often lacks Uzbek data ("2027 M07 25", "Wed"), so uz names are built by hand. Monday-based.
const UZ_WEEKDAYS: Record<"uz-Latn" | "uz-Cyrl", Record<"short" | "long", string[]>> = {
  "uz-Latn": {
    short: ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"],
    long: ["dushanba", "seshanba", "chorshanba", "payshanba", "juma", "shanba", "yakshanba"],
  },
  "uz-Cyrl": {
    short: ["Ду", "Се", "Чо", "Па", "Жу", "Ша", "Як"],
    long: ["душанба", "сешанба", "чоршанба", "пайшанба", "жума", "шанба", "якшанба"],
  },
};
/** Localized weekday name for a Monday-based index. */
export const weekdayName = (i: number, l: Locale, style: "short" | "long" = "short") =>
  isUz(l) ? UZ_WEEKDAYS[l][style][i]! : new Intl.DateTimeFormat(intlTag(l), { weekday: style }).format(new Date(2024, 0, 1 + i, 12));
const UZ_MONTHS: Record<"uz-Latn" | "uz-Cyrl", string[]> = {
  "uz-Latn": ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"],
  "uz-Cyrl": ["январ", "феврал", "март", "апрел", "май", "июн", "июл", "август", "сентябр", "октябр", "ноябр", "декабр"],
};
/** Localized date; uz is built by hand (see UZ_WEEKDAYS). */
export const formatDay = (iso: string, l: Locale, opts: Intl.DateTimeFormatOptions = { day: "numeric", month: "long" }) => {
  if (isUz(l) && (opts.month || opts.weekday)) {
    const d = fromISO(iso);
    const day = opts.day ? `${d.getDate()}-` : "";
    const month = opts.month ? UZ_MONTHS[l][d.getMonth()]! : "";
    const date = `${day}${month}${opts.year ? ` ${d.getFullYear()}` : ""}`.trim();
    const wd = opts.weekday ? weekdayName(weekdayOf(iso), l, opts.weekday === "long" ? "long" : "short") : "";
    return [date, wd].filter(Boolean).join(", ");
  }
  return new Intl.DateTimeFormat(intlTag(l), opts).format(fromISO(iso));
};

export const MIN_LEAD_DAYS = 14;
export const MAX_DAY_MINUTES = 150;
export const MIN_DAY_MINUTES = 10;

/** `null` when valid; otherwise why the start/exam pair is rejected. */
export type DatesError = "start_past" | "exam_too_soon";

export function datesError(today: string, start: string, exam: string): DatesError | null {
  if (!start || !exam) return "exam_too_soon";
  if (start < today) return "start_past";
  return daysBetween(start, exam) < MIN_LEAD_DAYS ? "exam_too_soon" : null;
}

/** Weekdays to send: the chosen ones minus the rest day. */
export const studyWeekdays = (weekdays: number[], rest: number | null) => weekdays.filter((d) => d !== rest).sort((a, b) => a - b);

export const clampMinutes = (n: number) => Math.min(MAX_DAY_MINUTES, Math.max(MIN_DAY_MINUTES, Math.round(n)));
