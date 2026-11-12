"use client";
import { useEffect, useRef, type ReactNode } from "react";
import { cn } from "../cn";
import { buttonClass } from "./Button";

export function Modal({
  open,
  onClose,
  title,
  children,
  className,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      aria-label={title}
      onClose={onClose}
      onClick={(e) => e.target === ref.current && onClose()}
      className={cn("m-auto w-[min(92vw,440px)] rounded-card border-2 border-line bg-white p-6 text-ink backdrop:bg-black/50", className)}
    >
      <h2 className="mb-3 text-2xl font-extrabold">{title}</h2>
      {children}
    </dialog>
  );
}

/** Accessible replacement for window.confirm(). */
export function ConfirmModal({
  open,
  title,
  message,
  confirmLabel,
  cancelLabel,
  danger,
  onConfirm,
  onClose,
}: {
  open: boolean;
  title: string;
  message?: ReactNode;
  confirmLabel: string;
  cancelLabel: string;
  danger?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}) {
  const cancelRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (open) cancelRef.current?.focus();
  }, [open]);
  return (
    <Modal open={open} onClose={onClose} title={title}>
      {message && <div className="mb-5 text-ink-soft">{message}</div>}
      <div className="flex flex-col gap-2 sm:flex-row-reverse">
        <button type="button" onClick={onConfirm} className={buttonClass(danger ? "danger" : "primary", true)}>
          {confirmLabel}
        </button>
        <button type="button" ref={cancelRef} onClick={onClose} className={buttonClass("secondary", true)}>
          {cancelLabel}
        </button>
      </div>
    </Modal>
  );
}
