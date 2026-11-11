"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import { buttonClass, cn, Modal } from "@dtmai/ui";
import { LocaleSwitcher, useT } from "@dtmai/i18n";
import { useAuth } from "@/lib/auth";
import { useBilling } from "@/lib/billing";
import { MAIN_NAV, MORE_NAV, TAB_NAV } from "./nav";
import { NavIcon } from "./NavIcon";
import { TopStats } from "./TopStats";

export function AppShell({ children }: { children: ReactNode }) {
  const t = useT();
  const path = usePathname();
  const { isGuest } = useAuth();
  const { canBuy } = useBilling();
  const [more, setMore] = useState(false);
  const active = (href: string) => path.startsWith(href.slice(0, -1));
  // Premium is a buy entry: hidden wherever the buy CTA is not allowed.
  const visible = (href: string) => href !== "/premium/" || canBuy;
  const moreItems = MORE_NAV.filter((n) => visible(n.href));
  const moreActive = moreItems.some((n) => active(n.href));

  return (
    <div className="min-h-dvh">
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col gap-2 border-r-2 border-line bg-white p-4 lg:flex">
        <Link href="/learn/" className="mb-4 px-3 text-3xl font-extrabold text-green">
          {t("app.name")}
        </Link>
        <nav className="flex flex-col gap-1" aria-label={t("nav.main")}>
          {MAIN_NAV.filter((n) => visible(n.href)).map((n) => (
            <Link
              key={n.href}
              href={n.href}
              aria-current={active(n.href) ? "page" : undefined}
              className={cn(
                "flex items-center gap-4 rounded-2xl border-2 px-4 py-3 text-[15px] font-extrabold uppercase tracking-wide",
                active(n.href) ? "border-blue bg-blue-soft text-blue" : "border-transparent text-ink-soft hover:bg-snow",
              )}
            >
              <NavIcon name={n.icon} />
              {t(n.label)}
            </Link>
          ))}
        </nav>
        <LocaleSwitcher className="mt-auto px-3" />
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex items-center justify-between border-b-2 border-line bg-white px-4 py-3 lg:justify-end">
          <span className="text-2xl font-extrabold text-green lg:hidden">{t("app.name")}</span>
          <div className="flex items-center gap-2 sm:gap-3">
            <TopStats />
            <LocaleSwitcher className="hidden sm:block lg:hidden" />
          </div>
        </header>
        {isGuest && (
          <div className="flex flex-wrap items-center justify-between gap-2 border-b-2 border-gold bg-snow px-4 py-2 text-sm font-bold text-ink">
            <span>{t("guest.banner")}</span>
            <Link href="/register/" className={buttonClass("primary", false, "px-3 py-1.5 text-xs")}>
              {t("guest.save")}
            </Link>
          </div>
        )}
        <main className="mx-auto max-w-3xl px-4 py-6 pb-28 lg:pb-10">{children}</main>
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-30 flex border-t-2 border-line bg-white pb-[env(safe-area-inset-bottom)] lg:hidden" aria-label={t("nav.main")}>
        {MAIN_NAV.filter((n) => TAB_NAV.includes(n.href)).map((n) => (
          <Link
            key={n.href}
            href={n.href}
            aria-label={t(n.label)}
            aria-current={active(n.href) ? "page" : undefined}
            className={cn("flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-extrabold", active(n.href) ? "text-blue" : "text-ink-soft")}
          >
            <NavIcon name={n.icon} size={26} />
            <span className="max-w-full truncate px-1">{t(n.label)}</span>
          </Link>
        ))}
        {moreItems.length > 0 && (
          <button
            type="button"
            aria-label={t("nav.more")}
            aria-haspopup="dialog"
            onClick={() => setMore(true)}
            className={cn("flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-extrabold", moreActive ? "text-blue" : "text-ink-soft")}
          >
            <NavIcon name="more" size={26} />
            <span className="max-w-full truncate px-1">{t("nav.more")}</span>
          </button>
        )}
      </nav>

      <Modal open={more} onClose={() => setMore(false)} title={t("nav.more")}>
        <ul className="flex flex-col gap-1">
          {moreItems.map((n) => (
            <li key={n.href}>
              <Link
                href={n.href}
                onClick={() => setMore(false)}
                aria-current={active(n.href) ? "page" : undefined}
                className="flex items-center gap-4 rounded-2xl px-3 py-3 font-extrabold text-ink hover:bg-snow"
              >
                <NavIcon name={n.icon} size={24} />
                {t(n.label)}
              </Link>
            </li>
          ))}
        </ul>
        <LocaleSwitcher className="mt-4" />
      </Modal>
    </div>
  );
}
