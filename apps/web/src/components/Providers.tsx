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
    // Next re-applies static metadata after hydration/navigation; re-assert the localized title whenever <title> changes, keeping page-specific titles ("X · Name").
    const want = t("app.title");
    const apply = () => {
      if ((pathname === "/" || !document.title.includes(" · ")) && document.title !== want) document.title = want;
    };
    apply();
    const obs = new MutationObserver(apply);
    obs.observe(document.head, { subtree: true, childList: true, characterData: true });
    document.querySelector('meta[name="description"]')?.setAttribute("content", t("app.description"));
    return () => obs.disconnect();
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
