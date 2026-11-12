import type { MessageKey } from "@dtmai/i18n";

type T = (key: MessageKey, vars?: Record<string, string | number>) => string;

/** Translation lookup by CLDR plural category: `<key>.one|few|many|other`, falling back to `.other`. */
export function tPlural(t: T, locale: string, key: string, n: number): string {
  const cat = new Intl.PluralRules(locale).select(n);
  const k = `${key}.${cat}` as MessageKey;
  const hit = t(k, { n });
  return hit === k ? t(`${key}.other` as MessageKey, { n }) : hit;
}
