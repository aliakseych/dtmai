"use client";
import { cn } from "@dtmai/ui";
import { useEffect, useRef, useState } from "react";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";
import { useT } from "@/lib/i18n";
import { errMsg } from "@/lib/util";

const field = "w-full rounded-xl border border-line bg-white px-2 py-1.5 text-sm outline-none focus:border-blue focus:ring-1 focus:ring-blue aria-[invalid=true]:border-red-deep disabled:bg-snow";

export function Input({ className, ...p }: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...p} className={cn(field, className)} />;
}
export function Textarea({ className, ...p }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...p} className={cn(field, "min-h-16 font-mono text-xs", className)} />;
}
export function Select({ className, children, ...p }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select {...p} className={cn(field, "pr-6", className)}>
      {children}
    </select>
  );
}

export function Field({ label, hint, error, children, className }: { label: string; hint?: string; error?: string; children: ReactNode; className?: string }) {
  const ref = useRef<HTMLLabelElement>(null);
  const [dismissed, setDismissed] = useState<string | undefined>();
  const shown = error && error !== dismissed ? error : undefined;
  useEffect(() => {
    const ctl = ref.current?.querySelector<HTMLElement>("input,select,textarea");
    if (!ctl) return;
    if (!shown) { ctl.removeAttribute("aria-invalid"); return; }
    ctl.setAttribute("aria-invalid", "true");
    const root = ref.current?.closest("[role=dialog],dialog,form") ?? document;
    if (root.querySelector("[aria-invalid=true]") === ctl) ctl.focus();
    const clear = () => setDismissed(error);
    ctl.addEventListener("input", clear, { once: true });
    return () => ctl.removeEventListener("input", clear);
  }, [shown, error]);
  return (
    <label ref={ref} className={cn("block", className)}>
      <span className="mb-0.5 block text-xs font-extrabold uppercase tracking-wide text-ink-soft">{label}</span>
      {children}
      {hint && <span className="mt-0.5 block text-xs font-semibold text-ink-soft">{hint}</span>}
      {shown && <span role="alert" className="mt-0.5 block text-xs font-bold text-red-deep">{shown}</span>}
    </label>
  );
}

export function Check({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label?: string }) {
  return (
    <label className="inline-flex cursor-pointer items-center gap-1.5 text-sm">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="size-4 accent-blue" />
      {label}
    </label>
  );
}

/** Localized file picker (the native control renders "Choose File" in the browser language). */
export function FileBtn({ accept, multiple, disabled, onFiles }: { accept?: string; multiple?: boolean; disabled?: boolean; onFiles: (files: FileList | null, input: HTMLInputElement) => void }) {
  const t = useT();
  const [name, setName] = useState("");
  return (
    <span className={cn("relative inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-xl border border-line bg-white px-3 text-sm font-extrabold hover:bg-snow focus-within:ring-1 focus-within:ring-blue", disabled && "cursor-not-allowed opacity-50")}>
      {t("admin.common.chooseFile")}
      {name && <span className="max-w-40 truncate text-xs font-semibold text-ink-soft">{name}</span>}
      <input type="file" accept={accept} multiple={multiple} disabled={disabled} className="absolute inset-0 size-full cursor-pointer opacity-0 disabled:cursor-not-allowed" onChange={(e) => { const i = e.target; setName(i.files?.length ? (i.files.length > 1 ? String(i.files.length) : i.files[0]!.name) : ""); onFiles(i.files, i); }} />
    </span>
  );
}

type Variant = "default" | "primary" | "danger" | "ghost";
const V: Record<Variant, string> = {
  default: "border-line bg-white hover:bg-snow",
  primary: "border-blue-deep bg-blue text-white hover:bg-blue-deep",
  danger: "border-red-deep bg-white text-red-deep hover:bg-red-soft",
  ghost: "border-transparent hover:bg-snow",
};
export function Btn({ variant = "default", className, ...p }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      type="button"
      {...p}
      className={cn("inline-flex min-h-11 items-center justify-center gap-1 rounded-xl border px-3 py-1.5 text-sm font-extrabold disabled:cursor-not-allowed disabled:opacity-50", V[variant], className)}
    />
  );
}

type Tone = "gray" | "green" | "red" | "blue" | "gold" | "orange";
const T: Record<Tone, string> = {
  gray: "bg-snow text-ink-soft border-line",
  green: "bg-green-soft text-green-deep border-green",
  red: "bg-red-soft text-red-deep border-red",
  blue: "bg-blue-soft text-blue-deep border-blue",
  gold: "bg-yellow-50 text-gold-deep border-gold",
  orange: "bg-orange-50 text-orange-deep border-orange",
};
export function Badge({ tone = "gray", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return <span className={cn("inline-flex items-center rounded-xl border px-1.5 py-px text-xs font-extrabold", T[tone], className)}>{children}</span>;
}

const STATUS_TONE: Record<string, Tone> = {
  verified: "green", published: "green", done: "green", active: "green",
  draft: "gray", pending: "gray", hidden: "gray", retired: "gray",
  auto_agreed: "blue", running: "blue",
  escalated: "orange", needs_human: "gold",
  failed: "red", archived: "gray",
};
export function StatusBadge({ status }: { status: string }) {
  const t = useT();
  const label = t(`admin.status.${status}`);
  return <Badge tone={STATUS_TONE[status] ?? "gray"}>{label === `admin.status.${status}` ? status : label}</Badge>;
}

export function Spinner() {
  return <span className="inline-block size-4 animate-spin rounded-full border-2 border-line border-t-blue" />;
}
export function PageHeader({ title, sub, actions }: { title: string; sub?: string; actions?: ReactNode }) {
  return (
    <div className="flex flex-col gap-2 border-b border-line bg-white px-3 py-3 sm:flex-row sm:items-end sm:justify-between sm:gap-3 sm:px-5">
      <div className="min-w-0">
        <h1 className="text-lg leading-tight">{title}</h1>
        {sub && <p className="text-xs text-ink-soft">{sub}</p>}
      </div>
      <div className="flex flex-wrap items-center gap-2">{actions}</div>
    </div>
  );
}
export function Toolbar({ children }: { children: ReactNode }) {
  return <div className="flex flex-wrap items-end gap-2 border-b border-line bg-white px-3 py-2 sm:px-5 max-sm:[&>label]:min-w-[40%] max-sm:[&>label]:flex-1">{children}</div>;
}
export function Empty({ children }: { children: ReactNode }) {
  return <div className="p-8 text-center text-ink-soft">{children}</div>;
}
export function ErrorBox({ error }: { error: unknown }) {
  return <div role="alert" className="m-4 rounded-xl border border-red bg-red-soft px-3 py-2 text-red-deep">{errMsg(error)}</div>;
}
export function Tabs<T extends string>({ value, onChange, items }: { value: T; onChange: (v: T) => void; items: { id: T; label: string }[] }) {
  return (
    <div role="tablist" className="flex gap-1 overflow-x-auto border-b border-line bg-white px-3 sm:px-5">
      {items.map((i) => (
        <button key={i.id} type="button" role="tab" aria-selected={value === i.id} onClick={() => onChange(i.id)} className={cn("-mb-px inline-flex min-h-11 shrink-0 items-center whitespace-nowrap border-b-2 px-3 py-2 text-sm font-extrabold", value === i.id ? "border-blue text-blue-deep" : "border-transparent text-ink-soft hover:text-ink")}>
          {i.label}
        </button>
      ))}
    </div>
  );
}
