"use client";
import { cn } from "@dtmai/ui";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

const field = "w-full rounded-md border border-line bg-white px-2 py-1.5 text-[13px] outline-none focus:border-blue focus:ring-1 focus:ring-blue disabled:bg-snow";

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
  return (
    <label className={cn("block", className)}>
      <span className="mb-0.5 block text-[11px] font-extrabold uppercase tracking-wide text-ink-soft">{label}</span>
      {children}
      {hint && <span className="mt-0.5 block text-[11px] font-semibold text-ink-soft">{hint}</span>}
      {error && <span className="mt-0.5 block text-[11px] font-bold text-red-deep">{error}</span>}
    </label>
  );
}

export function Check({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label?: string }) {
  return (
    <label className="inline-flex cursor-pointer items-center gap-1.5 text-[13px]">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="size-4 accent-blue" />
      {label}
    </label>
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
      className={cn("inline-flex items-center justify-center gap-1 rounded-md border px-2.5 py-1.5 text-[13px] font-extrabold disabled:cursor-not-allowed disabled:opacity-50", V[variant], className)}
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
  return <span className={cn("inline-flex items-center rounded border px-1.5 py-px text-[11px] font-extrabold", T[tone], className)}>{children}</span>;
}

const STATUS_TONE: Record<string, Tone> = {
  verified: "green", published: "green", done: "green", active: "green",
  draft: "gray", pending: "gray", hidden: "gray", retired: "gray",
  auto_agreed: "blue", running: "blue",
  escalated: "orange", needs_human: "gold",
  failed: "red", archived: "gray",
};
export const StatusBadge = ({ status }: { status: string }) => <Badge tone={STATUS_TONE[status] ?? "gray"}>{status}</Badge>;

export function Spinner() {
  return <span className="inline-block size-4 animate-spin rounded-full border-2 border-line border-t-blue" />;
}
export function PageHeader({ title, sub, actions }: { title: string; sub?: string; actions?: ReactNode }) {
  return (
    <div className="flex items-end justify-between gap-3 border-b border-line bg-white px-5 py-3">
      <div>
        <h1 className="text-lg leading-tight">{title}</h1>
        {sub && <p className="text-xs text-ink-soft">{sub}</p>}
      </div>
      <div className="flex items-center gap-2">{actions}</div>
    </div>
  );
}
export function Toolbar({ children }: { children: ReactNode }) {
  return <div className="flex flex-wrap items-end gap-2 border-b border-line bg-white px-5 py-2">{children}</div>;
}
export function Empty({ children }: { children: ReactNode }) {
  return <div className="p-8 text-center text-ink-soft">{children}</div>;
}
export function ErrorBox({ error }: { error: unknown }) {
  return <div className="m-4 rounded-md border border-red bg-red-soft px-3 py-2 text-red-deep">{error instanceof Error ? error.message : String(error)}</div>;
}
export function Tabs<T extends string>({ value, onChange, items }: { value: T; onChange: (v: T) => void; items: { id: T; label: string }[] }) {
  return (
    <div className="flex gap-1 border-b border-line bg-white px-5">
      {items.map((i) => (
        <button key={i.id} type="button" onClick={() => onChange(i.id)} className={cn("-mb-px border-b-2 px-3 py-2 text-[13px] font-extrabold", value === i.id ? "border-blue text-blue-deep" : "border-transparent text-ink-soft hover:text-ink")}>
          {i.label}
        </button>
      ))}
    </div>
  );
}
