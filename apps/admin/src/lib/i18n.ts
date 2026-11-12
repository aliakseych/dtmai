"use client";
import { useCallback } from "react";
import { translate, useLocale, type MessageKey } from "@dtmai/i18n";

export type TFn = (key: string, params?: Record<string, string | number>) => string;

/** Admin translator: `admin.*` keys live in the shared catalogue; missing keys fall back to uz-Latn, then the key. */
export function useT(): TFn {
  const { locale } = useLocale();
  return useCallback((key, params) => translate(locale, key as MessageKey, params), [locale]);
}

/** Localized label for a raw backend enum (`admin.enum.<group>.<value>`); unknown values render as-is. */
export function useEnum(): (group: string, value: string | null | undefined) => string {
  const t = useT();
  return useCallback((group, value) => {
    if (!value) return "—";
    const k = `admin.enum.${group}.${value}`;
    const r = t(k);
    return r === k || !r ? value : r;
  }, [t]);
}

export { useLocale };
