"use client";
import { cn } from "@dtmai/ui";
import { useEffect, type ReactNode } from "react";

function useEsc(open: boolean, onClose: () => void) {
  useEffect(() => {
    if (!open) return;
    const h = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [open, onClose]);
}

export function Drawer({ open, onClose, title, children, footer, width = "max-w-3xl" }: { open: boolean; onClose: () => void; title: ReactNode; children: ReactNode; footer?: ReactNode; width?: string }) {
  useEsc(open, onClose);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/30" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <aside role="dialog" aria-modal="true" className={cn("flex h-full w-full flex-col bg-white shadow-2xl", width)}>
        <header className="flex items-center justify-between border-b border-line px-4 py-2.5">
          <h2 className="text-base">{title}</h2>
          <button type="button" aria-label="Close" onClick={onClose} className="rounded px-2 py-1 text-lg leading-none hover:bg-snow">×</button>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto p-4">{children}</div>
        {footer && <footer className="flex items-center justify-end gap-2 border-t border-line px-4 py-2.5">{footer}</footer>}
      </aside>
    </div>
  );
}

export function Dialog({ open, onClose, title, children, footer, dismissable = true }: { open: boolean; onClose: () => void; title: ReactNode; children: ReactNode; footer?: ReactNode; dismissable?: boolean }) {
  useEsc(open && dismissable, onClose);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-4" onMouseDown={(e) => dismissable && e.target === e.currentTarget && onClose()}>
      <div role="dialog" aria-modal="true" className="w-full max-w-lg rounded-lg bg-white shadow-2xl">
        <header className="border-b border-line px-4 py-2.5"><h2 className="text-base">{title}</h2></header>
        <div className="p-4">{children}</div>
        {footer && <footer className="flex justify-end gap-2 border-t border-line px-4 py-2.5">{footer}</footer>}
      </div>
    </div>
  );
}
