"use client";
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { GbFlag, LanguageSelector, RuFlag, UzFlag } from "@dtmai/ui";
import { DEFAULT_LOCALE, LOCALES, LOCALE_LABELS, isLocale, translate, type Locale, type MessageKey } from "./locales";

const STORAGE_KEY = "dtmai.locale";

type Ctx = { locale: Locale; setLocale: (l: Locale) => void };
const LocaleContext = createContext<Ctx>({ locale: DEFAULT_LOCALE, setLocale: () => {} });

export function I18nProvider({ children, initial }: { children: ReactNode; initial?: Locale }) {
  const [locale, setLocaleState] = useState<Locale>(initial ?? DEFAULT_LOCALE);

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (isLocale(saved)) setLocaleState(saved);
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale === "uz-Latn" ? "uz" : locale === "uz-Cyrl" ? "uz-Cyrl" : locale;
  }, [locale]);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    window.localStorage.setItem(STORAGE_KEY, l);
  }, []);

  const value = useMemo(() => ({ locale, setLocale }), [locale, setLocale]);
  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useLocale(): Ctx {
  return useContext(LocaleContext);
}

export function useT() {
  const { locale } = useLocale();
  return useCallback(
    (key: MessageKey, params?: Record<string, string | number>) => translate(locale, key, params),
    [locale],
  );
}

const FLAGS: Record<Locale, ReactNode> = {
  "uz-Latn": <UzFlag />,
  "uz-Cyrl": <UzFlag />,
  ru: <RuFlag />,
  en: <GbFlag />,
};

export function LocaleSwitcher({
  className,
  placement,
  align,
}: {
  className?: string;
  placement?: "bottom" | "top";
  align?: "start" | "end";
}) {
  const { locale, setLocale } = useLocale();
  const t = useT();
  const options = useMemo(() => LOCALES.map((l) => ({ value: l, label: LOCALE_LABELS[l], flag: FLAGS[l] })), []);
  return (
    <LanguageSelector
      value={locale}
      options={options}
      onChange={(v) => setLocale(v as Locale)}
      label={t("language.site" as MessageKey)}
      placement={placement}
      align={align}
      className={className}
    />
  );
}
