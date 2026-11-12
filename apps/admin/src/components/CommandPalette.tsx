"use client";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { NAV } from "@/lib/nav";
import { useAuth } from "@/lib/auth";
import { useT } from "@/lib/i18n";

export function CommandPalette() {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [idx, setIdx] = useState(0);
  const router = useRouter();
  const { logout } = useAuth();
  const input = useRef<HTMLInputElement>(null);

  const all = useMemo(
    () => [
      ...NAV.flatMap((s) => s.items.map((i) => ({ id: i.href, label: t(i.label), group: t(s.title), hay: `${t(i.label)} ${i.keywords ?? ""}`.toLowerCase(), run: () => router.push(i.href) }))),
      { id: "new-question", label: t("admin.palette.newQuestion"), group: t("admin.palette.actions"), hay: `new question create add ${t("admin.palette.newQuestion")}`.toLowerCase(), run: () => router.push("/questions/?new=1") },
      { id: "logout", label: t("admin.common.signOut"), group: t("admin.palette.actions"), hay: `sign out logout ${t("admin.common.signOut")}`.toLowerCase(), run: () => void logout() },
    ],
    [router, logout, t],
  );
  const hits = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return all;
    const rank = (l: string) => (l === needle ? 0 : l.startsWith(needle) ? 1 : 2);
    return all
      .filter((a) => needle.split(/\s+/).every((w) => a.hay.includes(w)))
      .sort((a, b) => rank(a.label.toLowerCase()) - rank(b.label.toLowerCase()));
  }, [all, q]);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
        setQ("");
        setIdx(0);
      } else if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);
  useEffect(() => {
    if (open) input.current?.focus();
  }, [open]);

  if (!open) return null;
  const go = (i: number) => {
    hits[i]?.run();
    setOpen(false);
  };
  return (
    <div className="fixed inset-0 z-[60] grid place-items-start justify-center bg-black/30 pt-[15vh]" onMouseDown={(e) => e.target === e.currentTarget && setOpen(false)}>
      <div role="dialog" aria-label={t("admin.palette.title")} className="w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-2xl">
        <input
          ref={input}
          value={q}
          placeholder={t("admin.palette.placeholder")}
          onChange={(e) => { setQ(e.target.value); setIdx(0); }}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") { e.preventDefault(); setIdx((i) => Math.min(i + 1, hits.length - 1)); }
            if (e.key === "ArrowUp") { e.preventDefault(); setIdx((i) => Math.max(i - 1, 0)); }
            if (e.key === "Enter") go(idx);
          }}
          className="w-full border-b border-line px-4 py-3 text-sm outline-none"
        />
        <ul className="max-h-80 overflow-y-auto py-1">
          {hits.length === 0 && <li className="px-4 py-3 text-ink-soft">{t("admin.palette.noMatches")}</li>}
          {hits.map((h, i) => (
            <li key={h.id}>
              <button type="button" onMouseEnter={() => setIdx(i)} onClick={() => go(i)} className={`flex w-full items-center justify-between px-4 py-1.5 text-left ${i === idx ? "bg-blue-soft" : ""}`}>
                <span>{h.label}</span>
                <span className="text-xs text-ink-soft">{h.group}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
