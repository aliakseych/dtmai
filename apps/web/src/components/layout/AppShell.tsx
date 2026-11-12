"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { Avatar, buttonClass, cn, Logo, Mascot, Modal, Icon } from "@dtmai/ui";
import { LocaleSwitcher, useT } from "@dtmai/i18n";
import { useAuth } from "@/lib/auth";
import { useBilling } from "@/lib/billing";
import { MAIN_NAV, MORE_NAV, TAB_NAV } from "./nav";
import { QuestsPanel } from "./QuestsPanel";
import { TopStats } from "./TopStats";

export function AppShell({ children }: { children: ReactNode }) {
  const t = useT();
  const path = usePathname();
  const router = useRouter();
  const { isGuest, me } = useAuth();
  // Account gate: a guest who finished onboarding must create an account (or sign in) before using the app; the plan stays reachable.
  const gated = isGuest && !path.startsWith("/plan") && !path.startsWith("/account");
  useEffect(() => {
    if (gated) router.replace("/account/");
  }, [gated, router]);
  const { canBuy } = useBilling();
  const [more, setMore] = useState(false);
  const active = (href: string) => path.startsWith(href.slice(0, -1));
  // Premium is a buy entry: hidden wherever the buy CTA is not allowed.
  // The representative portal is shown only to users holding the lyceum_rep role.
  const isRep = !!me?.roles.includes("lyceum_rep");
  const visible = (href: string) => (href !== "/premium/" || canBuy) && (href !== "/rep/" || isRep);
  const moreItems = MORE_NAV.filter((n) => visible(n.href));
  const moreActive = moreItems.some((n) => active(n.href));

  if (gated) return <div className="grid min-h-dvh place-items-center" aria-busy="true" />;

  return (
    <div className="min-h-dvh overflow-x-clip bg-white">
      <aside className="fixed inset-y-0 left-0 hidden w-72 flex-col gap-2 overflow-y-auto border-r-2 border-line bg-white p-4 lg:flex">
        <Link href="/learn/" aria-label={t("app.name")} className="mb-4 px-3 pt-1">
          <Logo name={t("app.name")} size={36} />
        </Link>
        <nav className="flex flex-col gap-1" aria-label={t("nav.main")}>
          {MAIN_NAV.filter((n) => visible(n.href)).map((n) => (
            <Link
              key={n.href}
              href={n.href}
              aria-current={active(n.href) ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-2xl border-2 px-4 py-2 text-[15px] font-extrabold uppercase tracking-wide transition active:scale-[0.98]",
                active(n.href) ? "border-brand bg-brand-soft text-brand" : "border-transparent text-ink-soft hover:bg-snow hover:text-ink",
              )}
            >
              <Icon name={n.icon} size={24} />
              {t(n.label)}
            </Link>
          ))}
        </nav>
        <div className="mt-auto flex flex-col gap-3 border-t-2 border-line pt-3">
          {me && (
            <Link href="/profile/" className="flex items-center gap-3 rounded-2xl border-2 border-transparent px-3 py-2 transition hover:bg-snow active:scale-[0.98]">
              <Avatar name={me.name} size={36} />
              <span className="truncate text-[15px] font-extrabold text-ink">{me.name}</span>
            </Link>
          )}
          <LocaleSwitcher className="max-w-full" placement="top" align="start" />
        </div>
      </aside>

      <div className="lg:pl-72">
        <header className="sticky top-0 z-20 flex items-center justify-between gap-2 border-b-2 border-line bg-white/95 px-4 py-2 backdrop-blur lg:hidden">
          <Link href="/learn/" aria-label={t("app.name")}>
            <Logo name={t("app.name")} size={28} />
          </Link>
          <div className="flex items-center gap-2">
            <TopStats />
            <LocaleSwitcher className="hidden md:block" align="end" />
          </div>
        </header>
        <div className="mx-auto flex max-w-5xl justify-center gap-8 px-4 py-6 pb-28 lg:pb-10">
          <main className="min-w-0 max-w-3xl flex-1">{children}</main>
          <aside className="sticky top-6 hidden h-fit w-80 shrink-0 flex-col gap-4 xl:flex" aria-label={t("nav.more")}>
            <div className="flex justify-end">
              <TopStats />
            </div>
            <QuestsPanel />
            {canBuy && (
              <div className="flex flex-col items-center gap-3 rounded-card bg-brand p-5 text-center text-white">
                <Mascot mood="premium" size={96} alt={t("mascot.alt")} className="h-auto w-24" />
                <h2 className="text-lg">{t("plan.premium.name")}</h2>
                <p className="text-sm font-bold text-white/80">{t("landing.pricing.subtitle")}</p>
                <Link href="/premium/" className={buttonClass("super", true)}>
                  {t("plan.premium.cta")}
                </Link>
              </div>
            )}
          </aside>
        </div>
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-30 flex border-t-2 border-line bg-white pb-[env(safe-area-inset-bottom)] lg:hidden" aria-label={t("nav.main")}>
        {MAIN_NAV.filter((n) => TAB_NAV.includes(n.href)).map((n) => (
          <Link
            key={n.href}
            href={n.href}
            aria-label={t(n.label)}
            aria-current={active(n.href) ? "page" : undefined}
            className={cn("flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-extrabold", active(n.href) ? "text-brand" : "text-ink-soft")}
          >
            <span className={cn("grid h-11 w-12 place-items-center rounded-xl transition", active(n.href) && "bg-brand-soft")}>
              <Icon name={n.icon} />
            </span>
            <span className="max-w-full truncate px-1">{t(n.label)}</span>
          </Link>
        ))}
        {moreItems.length > 0 && (
          <button
            type="button"
            aria-label={t("nav.more")}
            aria-haspopup="dialog"
            onClick={() => setMore(true)}
            className={cn("flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-extrabold", moreActive ? "text-brand" : "text-ink-soft")}
          >
            <span className={cn("grid h-11 w-12 place-items-center rounded-xl transition", moreActive && "bg-brand-soft")}>
              <Icon name="more" />
            </span>
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
                <Icon name={n.icon} />
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
