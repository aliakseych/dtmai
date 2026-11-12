"use client";
import Link from "next/link";
import { useId, useState, type ReactNode } from "react";
import { LocaleSwitcher, useT } from "@dtmai/i18n";
import { Logo, Mascot } from "@dtmai/ui";
import { useDocumentTitle } from "@/components/PageTitle";

export function AuthFrame({ title, children, footer }: { title: string; children: ReactNode; footer: ReactNode }) {
  const t = useT();
  useDocumentTitle(title);
  return (
    <div className="mx-auto flex min-h-dvh max-w-md flex-col justify-center gap-4 px-4 py-6 sm:gap-6 sm:py-8">
      <div className="flex items-center justify-between">
        <Link href="/" aria-label={t("app.name")} className="inline-flex min-h-11 items-center">
          <Logo name={t("app.name")} size={40} />
        </Link>
        <LocaleSwitcher />
      </div>
      <Mascot mood="wave" size={120} alt={t("mascot.alt")} className="mx-auto h-auto w-20 sm:w-28" />
      <h1 className="text-center text-2xl sm:text-3xl">{title}</h1>
      {children}
      <p className="text-center text-ink-soft">{footer}</p>
    </div>
  );
}

export function Field({
  label,
  error,
  hint,
  reveal,
  type,
  ...rest
}: { label: string; error?: string | null; hint?: string; reveal?: boolean } & React.InputHTMLAttributes<HTMLInputElement>) {
  const t = useT();
  const id = useId();
  const [shown, setShown] = useState(false);
  const describedBy = [error ? `${id}-err` : null, hint ? `${id}-hint` : null].filter(Boolean).join(" ") || undefined;
  return (
    <div className="flex flex-col gap-1 text-sm font-extrabold text-ink-soft">
      <label htmlFor={id}>{label}</label>
      <div className="relative">
        <input
          {...rest}
          id={id}
          type={reveal && shown ? "text" : type}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={`w-full rounded-2xl border-2 bg-snow px-4 py-3 text-base font-bold text-ink focus:border-brand focus:bg-white ${
            error ? "border-red-deep" : "border-line"
          } ${reveal ? "pr-24" : ""}`}
        />
        {reveal && (
          <button
            type="button"
            aria-pressed={shown}
            onClick={() => setShown((v) => !v)}
            className="absolute right-1 top-1/2 grid min-h-11 -translate-y-1/2 place-items-center px-2 text-sm font-extrabold text-brand underline"
          >
            {shown ? t("auth.password.hide") : t("auth.password.show")}
          </button>
        )}
      </div>
      {hint && !error && (
        <p id={`${id}-hint`} className="font-bold">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-err`} className="font-bold text-red-deep">
          {error}
        </p>
      )}
    </div>
  );
}
