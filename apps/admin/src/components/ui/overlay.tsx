"use client";
import { Icon, cn } from "@dtmai/ui";
import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { useT } from "@/lib/i18n";
import { useConfirm } from "./confirm";

/** Esc closes; ignored while a native confirm <dialog> is on top (it handles its own Esc). `preventDefault` stops the
 * browser from cancelling a confirm <dialog> opened by this same keypress. */
function useEsc(open: boolean, onClose: () => void) {
  useEffect(() => {
    if (!open) return;
    const h = (e: KeyboardEvent) => {
      if (e.key !== "Escape" || document.querySelector("dialog[open]")) return;
      e.preventDefault();
      onClose();
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [open, onClose]);
}

/** Dirty tracking + discard confirm shared by Drawer and Dialog. */
function useDiscardGuard(open: boolean, onClose: () => void, dirty?: boolean) {
  const t = useT();
  const [touched, setTouched] = useState(false);
  const [ask, confirmNode] = useConfirm();
  useEffect(() => { if (open) setTouched(false); }, [open]);
  const isDirty = dirty ?? touched;
  const request = () => (isDirty ? ask({ title: t("admin.common.discardTitle"), body: t("admin.common.discardBody"), confirmLabel: t("admin.common.discard"), cancelLabel: t("admin.common.keepEditing"), danger: true }, onClose) : onClose());
  return { request, confirmNode, touch: () => setTouched(true) };
}

const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]):not([type=hidden]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';

/** Locks body scroll, moves focus inside, traps Tab and restores focus on close. */
export function useModalFocus(open: boolean, ref: React.RefObject<HTMLElement | null>) {
  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const el = ref.current;
    if (el && !el.contains(document.activeElement)) (el.querySelector<HTMLElement>("[data-modal-body] :is(input,select,textarea):not([disabled]):not([type=hidden])") ?? el.querySelector<HTMLElement>(FOCUSABLE) ?? el).focus();
    const trap = (e: KeyboardEvent) => {
      if (e.key !== "Tab" || !el || document.querySelector("dialog[open]")) return;
      const f = Array.from(el.querySelectorAll<HTMLElement>(FOCUSABLE));
      if (!f.length) return;
      const first = f[0]!, last = f[f.length - 1]!;
      if (e.shiftKey && (document.activeElement === first || !el.contains(document.activeElement))) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && (document.activeElement === last || !el.contains(document.activeElement))) { e.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", trap);
    return () => { document.removeEventListener("keydown", trap); document.body.style.overflow = overflow; prev?.focus?.(); };
  }, [open, ref]);
}

/**
 * Side drawer. Dirty-state guard: any input/change inside marks it dirty (or pass `dirty`); closing a dirty
 * drawer by Esc, backdrop or ✕ asks to discard first.
 */
export function Drawer({ open, onClose, title, children, footer, width = "max-w-3xl", dirty }: { open: boolean; onClose: () => void; title: ReactNode; children: ReactNode; footer?: ReactNode; width?: string; dirty?: boolean }) {
  const t = useT();
  const { request, confirmNode, touch } = useDiscardGuard(open, onClose, dirty);
  const ref = useRef<HTMLElement>(null);
  const titleId = useId();
  useEsc(open, request);
  useModalFocus(open, ref);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/30" onMouseDown={(e) => e.target === e.currentTarget && request()}>
      <aside ref={ref} role="dialog" aria-modal="true" aria-labelledby={titleId} onInput={touch} onChange={touch} className={cn("flex h-full w-full flex-col bg-white", width)}>
        <header className="flex items-center justify-between gap-2 border-b border-line px-4 py-2.5">
          <h2 id={titleId} className="min-w-0 break-words text-base">{title}</h2>
          <button type="button" aria-label={t("admin.common.close")} onClick={request} className="grid size-11 shrink-0 place-items-center rounded-xl hover:bg-snow"><Icon name="close" size={20} /></button>
        </header>
        <div data-modal-body className="min-h-0 flex-1 overflow-y-auto p-4">{children}</div>
        {footer && <footer className="flex flex-wrap items-center justify-end gap-2 border-t border-line px-4 py-2.5">{footer}</footer>}
      </aside>
      {confirmNode}
    </div>
  );
}

export function Dialog({ open, onClose, title, children, footer, dismissable = true, dirty }: { open: boolean; onClose: () => void; title: ReactNode; children: ReactNode; footer?: ReactNode; dismissable?: boolean; dirty?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const { request, confirmNode, touch } = useDiscardGuard(open, onClose, dirty);
  useEsc(open && dismissable, request);
  useModalFocus(open, ref);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-4" onMouseDown={(e) => dismissable && e.target === e.currentTarget && request()}>
      <div ref={ref} role="dialog" aria-modal="true" aria-labelledby={titleId} onInput={touch} onChange={touch} className="max-h-full w-full max-w-lg overflow-y-auto rounded-card bg-white">
        <header className="border-b border-line px-4 py-2.5"><h2 id={titleId} className="text-base">{title}</h2></header>
        <div data-modal-body className="p-4">{children}</div>
        {footer && <footer className="flex flex-wrap justify-end gap-2 border-t border-line px-4 py-2.5">{footer}</footer>}
      </div>
      {confirmNode}
    </div>
  );
}
