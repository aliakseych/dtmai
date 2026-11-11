import type { Locale } from "@dtmai/i18n";

const tag = (l: Locale) => (l === "uz-Latn" ? "uz-Latn-UZ" : l === "uz-Cyrl" ? "uz-Cyrl-UZ" : l);
const utc = (iso: string) => new Date(`${iso.slice(0, 10)}T00:00:00Z`);

/** Day of month for axis ticks. */
export const dayLabel = (iso: string) => String(utc(iso).getUTCDate());

/** "12 Nov" style date, locale aware. */
export const shortDate = (iso: string, l: Locale) =>
  new Intl.DateTimeFormat(tag(l), { day: "numeric", month: "short", timeZone: "UTC" }).format(utc(iso));

/** Short weekday names Monday..Sunday. */
export const weekdayNames = (l: Locale) => {
  const f = new Intl.DateTimeFormat(tag(l), { weekday: "short", timeZone: "UTC" });
  return Array.from({ length: 7 }, (_, i) => f.format(new Date(Date.UTC(2024, 0, 1 + i)))); // 2024-01-01 is a Monday
};

/** Monday-first weekday index (0..6). */
export const weekdayIndex = (iso: string) => (utc(iso).getUTCDay() + 6) % 7;
