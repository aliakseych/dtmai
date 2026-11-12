"use client";
import Link from "next/link";
import { buttonClass, Logo, Icon } from "@dtmai/ui";
import { LocaleSwitcher, useT } from "@dtmai/i18n";

const LINKS = [
  ["#features", "landing.nav.features"],
  ["#pricing", "landing.nav.pricing"],
  ["#faq", "landing.nav.faq"],
] as const;

export function LandingHeader() {
  const t = useT();
  return (
    <header className="sticky top-0 z-30 border-b-2 border-line bg-white/95">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-2 px-4 py-3">
        <Link href="/" aria-label={t("app.name")}>
          <Logo name={t("app.name")} size={32} />
        </Link>
        <nav className="hidden gap-6 text-sm font-extrabold uppercase text-ink-soft md:flex" aria-label={t("nav.main")}>
          {LINKS.map(([href, key]) => (
            <a key={href} href={href}>
              {t(key)}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <div className="hidden sm:block">
            <LocaleSwitcher />
          </div>
          <Link href="/login/" className={buttonClass("secondary", false, "hidden sm:inline-flex")}>
            {t("auth.login.cta")}
          </Link>
          <Link href="/onboarding/" className={buttonClass("primary", false, "px-3 text-xs sm:px-5 sm:text-sm")}>
            {t("landing.header.start")}
          </Link>
          <details className="relative md:hidden">
            <summary aria-label={t("nav.menu")} className="grid h-10 w-10 cursor-pointer list-none place-items-center rounded-xl border-2 border-line">
              <Icon name="menu" />
            </summary>
            <div className="absolute right-0 top-12 flex w-52 flex-col gap-1 rounded-card border-2 border-line bg-white p-2 shadow-xl">
              {LINKS.map(([href, key]) => (
                <a key={href} href={href} className="rounded-xl px-3 py-2 font-extrabold text-ink hover:bg-snow">
                  {t(key)}
                </a>
              ))}
              <Link href="/login/" className="rounded-xl px-3 py-2 font-extrabold text-ink hover:bg-snow">
                {t("auth.login.cta")}
              </Link>
              <div className="px-3 py-2 sm:hidden">
                <LocaleSwitcher className="max-w-full" placement="bottom" align="end" />
              </div>
            </div>
          </details>
        </div>
      </div>
    </header>
  );
}
