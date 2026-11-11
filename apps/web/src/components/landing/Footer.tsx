"use client";
import { useT } from "@dtmai/i18n";

export function Footer() {
  const t = useT();
  return (
    <footer className="border-t-2 border-line py-8 text-center text-sm text-ink-soft">
      © {new Date().getFullYear()} {t("app.name")} · {t("landing.footer.rights")}
    </footer>
  );
}
