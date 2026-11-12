"use client";
import { Icon, Logo, cn } from "@dtmai/ui";
import { LocaleSwitcher } from "@dtmai/i18n";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { useAuth } from "@/lib/auth";
import { useT } from "@/lib/i18n";
import { NAV } from "@/lib/nav";
import { useModalFocus } from "@/components/ui/overlay";
import { CommandPalette } from "./CommandPalette";

/** Section links (scrolls) + pinned footer. Shared by the desktop sidebar and the mobile drawer. */
function NavBody({ path }: { path: string }) {
  const t = useT();
  const { me, logout } = useAuth();
  return (
    <>
      <div className="hidden shrink-0 items-center gap-2 px-4 py-3 md:flex"><Logo tone="brand" size={28} /><span className="text-sm font-extrabold text-ink-soft">{t("admin.shell.admin")}</span></div>
      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-2">
        {NAV.map((s) => (
          <div key={s.title} className="mb-2">
            <div className="px-2 py-1 text-xs font-extrabold uppercase tracking-wider text-ink-soft">{t(s.title)}</div>
            {s.items.map((i) => (
              <Link key={i.href} href={i.href} className={cn("flex min-h-11 items-center rounded-xl px-2 text-sm", path.startsWith(i.href.slice(0, -1)) ? "bg-blue-soft font-extrabold text-blue-deep" : "hover:bg-snow")}>
                {t(i.label)}
              </Link>
            ))}
          </div>
        ))}
      </div>
      <div className="shrink-0 border-t border-line bg-white px-3 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2 text-xs">
        <div className="hidden min-w-0 max-w-full overflow-hidden md:block"><LocaleSwitcher placement="top" compact /></div>
        <div className="truncate pt-1 font-extrabold">{me?.name || me?.email}</div>
        <div className="text-ink-soft">{me?.roles.join(", ")} · <kbd className="hidden rounded border border-line px-1 md:inline">⌘K</kbd></div>
        <button type="button" className="inline-flex min-h-11 items-center text-red-deep hover:underline" onClick={() => void logout()}>{t("admin.common.signOut")}</button>
      </div>
    </>
  );
}

export function Shell({ children }: { children: ReactNode }) {
  const path = usePathname();
  const t = useT();
  const [open, setOpen] = useState(false);
  const drawer = useRef<HTMLDivElement>(null);
  useEffect(() => setOpen(false), [path]);
  useEffect(() => {
    if (!open) return;
    const h = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [open]);
  useModalFocus(open, drawer);
  return (
    <div className="flex h-dvh w-full max-w-full flex-col overflow-x-hidden md:flex-row">
      <header className="flex items-center gap-3 border-b border-line bg-white px-3 py-2 md:hidden">
        <button type="button" aria-label={t("admin.shell.menu")} aria-expanded={open} aria-haspopup="dialog" onClick={() => setOpen(true)} className="grid size-11 shrink-0 place-items-center rounded-xl border border-line"><Icon name="menu" size={20} /></button>
        <Logo tone="brand" size={26} />
        <span className="min-w-0 flex-1 truncate text-sm font-extrabold text-ink-soft">{t("admin.shell.admin")}</span>
        <LocaleSwitcher align="end" />
      </header>
      <nav aria-label={t("admin.shell.navigation")} className="hidden min-h-0 w-52 shrink-0 flex-col border-r border-line bg-white md:flex">
        <NavBody path={path} />
      </nav>
      {open && (
        <div ref={drawer} role="dialog" aria-modal="true" aria-label={t("admin.shell.navigation")} className="fixed inset-0 z-40 flex flex-col bg-white md:hidden">
          <div className="flex shrink-0 items-center gap-3 border-b border-line px-3 py-2">
            <button type="button" aria-label={t("admin.common.close")} onClick={() => setOpen(false)} className="grid size-11 shrink-0 place-items-center rounded-xl border border-line"><Icon name="close" size={20} /></button>
            <Logo tone="brand" size={26} />
            <span className="min-w-0 flex-1 truncate text-sm font-extrabold text-ink-soft">{t("admin.shell.admin")}</span>
            <LocaleSwitcher align="end" />
          </div>
          <nav aria-label={t("admin.shell.navigation")} className="flex min-h-0 flex-1 flex-col"><NavBody path={path} /></nav>
        </div>
      )}
      <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">{children}</main>
      <CommandPalette />
    </div>
  );
}
