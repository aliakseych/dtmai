"use client";
import { useEffect, type ReactNode } from "react";
import { ToastProvider } from "@dtmai/ui";
import { I18nProvider, useT } from "@dtmai/i18n";
import { AuthProvider } from "@/lib/auth";

/** Localized document title/description (static export has no per-request metadata). */
function LocaleHead() {
  const t = useT();
  useEffect(() => {
    document.title = t("app.title");
    document.querySelector('meta[name="description"]')?.setAttribute("content", t("app.description"));
  }, [t]);
  return null;
}

export function Providers({ children }: { children: ReactNode }) {
  return (
    <I18nProvider>
      <ToastProvider>
        <AuthProvider>
          <LocaleHead />
          {children}
        </AuthProvider>
      </ToastProvider>
    </I18nProvider>
  );
}
