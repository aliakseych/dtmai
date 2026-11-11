"use client";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { NAV } from "@/lib/nav";
import { useAuth } from "@/lib/auth";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [idx, setIdx] = useState(0);
  const router = useRouter();
  const { logout } = useAuth();
  const input = useRef<HTMLInputElement>(null);

  const all = useMemo(
    () => [
      ...NAV.flatMap((s) => s.items.map((i) => ({ id: i.href, label: i.label, group: s.title, hay: `${i.label} ${i.keywords ?? ""}`.toLowerCase(), run: () => router.push(i.href) }))),
      { id: "new-question", label: "New question", group: "Actions", hay: "new question create add", run: () => router.push("/questions/?new=1") },
      { id: "logout", label: "Sign out", group: "Actions", hay: "sign out logout", run: () => void logout() },
    ],
    [router, logout],
  );
  const hits = useMemo(() => {
    const t = q.trim().toLowerCase();
    return t ? all.filter((a) => t.split(/\s+/).every((w) => a.hay.includes(w))) : all;
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
      <div role="dialog" aria-label="Command palette" className="w-full max-w-md overflow-hidden rounded-lg bg-white shadow-2xl">
        <input
          ref={input}
          value={q}
          placeholder="Jump to…"
          onChange={(e) => { setQ(e.target.value); setIdx(0); }}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") { e.preventDefault(); setIdx((i) => Math.min(i + 1, hits.length - 1)); }
            if (e.key === "ArrowUp") { e.preventDefault(); setIdx((i) => Math.max(i - 1, 0)); }
            if (e.key === "Enter") go(idx);
          }}
          className="w-full border-b border-line px-4 py-3 text-sm outline-none"
        />
        <ul className="max-h-80 overflow-y-auto py-1">
          {hits.length === 0 && <li className="px-4 py-3 text-ink-soft">No matches</li>}
          {hits.map((h, i) => (
            <li key={h.id}>
              <button type="button" onMouseEnter={() => setIdx(i)} onClick={() => go(i)} className={`flex w-full items-center justify-between px-4 py-1.5 text-left ${i === idx ? "bg-blue-soft" : ""}`}>
                <span>{h.label}</span>
                <span className="text-[11px] text-ink-soft">{h.group}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
