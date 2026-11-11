"use client";
import { Logo } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";

export function Footer() {
  const t = useT();
  return (
    <footer className="flex flex-col items-center gap-3 border-t-2 border-line py-8 text-center text-sm text-ink-soft">
      <Logo name={t("app.name")} size={28} />
      <span>© {new Date().getFullYear()} {t("app.name")} · {t("landing.footer.rights")}</span>
    </footer>
  );
}
