"use client";
import { Logo, cn } from "@dtmai/ui";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { useAuth } from "@/lib/auth";
import { NAV } from "@/lib/nav";
import { CommandPalette } from "./CommandPalette";

export function Shell({ children }: { children: ReactNode }) {
  const path = usePathname();
  const { me, logout } = useAuth();
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [path]);
  return (
    <div className="flex h-dvh flex-col md:flex-row">
      <header className="flex items-center gap-3 border-b border-line bg-white px-3 py-2 md:hidden">
        <button type="button" aria-label="Menu" aria-expanded={open} onClick={() => setOpen((o) => !o)} className="grid size-9 place-items-center rounded-md border border-line text-lg">☰</button>
        <Logo tone="brand" size={26} />
        <span className="text-sm font-extrabold text-ink-soft">admin</span>
      </header>
      <nav className={cn("min-h-0 shrink-0 flex-col overflow-y-auto border-line bg-white max-md:flex-1 md:flex md:w-52 md:border-r", open ? "flex" : "hidden")}>
        <div className="hidden items-center gap-2 px-4 py-3 md:flex"><Logo tone="brand" size={28} /><span className="text-sm font-extrabold text-ink-soft">admin</span></div>
        <div className="flex-1 px-2 pb-2">
          {NAV.map((s) => (
            <div key={s.title} className="mb-2">
              <div className="px-2 py-1 text-[10px] font-extrabold uppercase tracking-wider text-ink-soft">{s.title}</div>
              {s.items.map((i) => (
                <Link key={i.href} href={i.href} className={cn("block rounded-md px-2 py-1 text-[13px]", path.startsWith(i.href.slice(0, -1)) ? "bg-blue-soft font-extrabold text-blue-deep" : "hover:bg-snow")}>
                  {i.label}
                </Link>
              ))}
            </div>
          ))}
        </div>
        <div className="border-t border-line p-3 text-xs">
          <div className="truncate font-extrabold">{me?.name || me?.email}</div>
          <div className="text-ink-soft">{me?.roles.join(", ")} · <kbd className="rounded border border-line px-1">⌘K</kbd></div>
          <button type="button" className="mt-1 text-red-deep hover:underline" onClick={() => void logout()}>Sign out</button>
        </div>
      </nav>
      <main className={cn("min-h-0 min-w-0 flex-1 flex-col overflow-hidden", open ? "hidden md:flex" : "flex")}>{children}</main>
      <CommandPalette />
    </div>
  );
}
