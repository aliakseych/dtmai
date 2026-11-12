"use client";
import { useEffect, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { ToastProvider } from "@dtmai/ui";
import { I18nProvider, useT } from "@dtmai/i18n";
import { AuthProvider } from "@/lib/auth";

/** Localized document title/description (static export has no per-request metadata). */
function LocaleHead() {
  const t = useT();
  const pathname = usePathname();
  useEffect(() => {
    // Defer so Next's static metadata (applied on hydration/navigation) cannot win; keep page-specific titles ("X · Name").
    const id = window.setTimeout(() => {
      if (pathname === "/" || !document.title.includes(" · ")) document.title = t("app.title");
    }, 0);
    document.querySelector('meta[name="description"]')?.setAttribute("content", t("app.description"));
    return () => window.clearTimeout(id);
  }, [t, pathname]);
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
