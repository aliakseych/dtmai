import type { Locale } from "@dtmai/i18n";
import { formatDay, weekdayName } from "@/lib/planDates";

const utc = (iso: string) => new Date(`${iso.slice(0, 10)}T00:00:00Z`);

/** Day of month for axis ticks. */
export const dayLabel = (iso: string) => String(utc(iso).getUTCDate());

/** "12-noyabr" style date; uz is hand-built because browser ICU lacks Uzbek data ("M11 12"). */
export const shortDate = (iso: string, l: Locale) => formatDay(iso.slice(0, 10), l, { day: "numeric", month: "short" });

/** Short weekday names Monday..Sunday. */
export const weekdayNames = (l: Locale) => Array.from({ length: 7 }, (_, i) => weekdayName(i, l));

/** Monday-first weekday index (0..6). */
export const weekdayIndex = (iso: string) => (utc(iso).getUTCDay() + 6) % 7;
