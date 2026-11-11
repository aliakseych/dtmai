"use client";
import { cn } from "@dtmai/ui";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useAuth } from "@/lib/auth";
import { NAV } from "@/lib/nav";
import { CommandPalette } from "./CommandPalette";

export function Shell({ children }: { children: ReactNode }) {
  const path = usePathname();
  const { me, logout } = useAuth();
  return (
    <div className="flex h-screen">
      <nav className="flex w-52 shrink-0 flex-col overflow-y-auto border-r border-line bg-white">
        <div className="px-4 py-3 text-base font-extrabold text-brand">DTM AI <span className="text-ink-soft">admin</span></div>
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
      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">{children}</main>
      <CommandPalette />
    </div>
  );
}
