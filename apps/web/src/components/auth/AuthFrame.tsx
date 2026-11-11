"use client";
import Link from "next/link";
import type { ReactNode } from "react";
import { LocaleSwitcher, useT } from "@dtmai/i18n";
import { Mascot } from "@dtmai/ui";

export function AuthFrame({ title, children, footer }: { title: string; children: ReactNode; footer: ReactNode }) {
  const t = useT();
  return (
    <div className="mx-auto flex min-h-dvh max-w-md flex-col justify-center gap-6 px-4 py-8">
      <div className="flex items-center justify-between">
        <Link href="/" className="text-3xl font-extrabold text-green">
          {t("app.name")}
        </Link>
        <LocaleSwitcher />
      </div>
      <Mascot mood="wave" size={120} alt={t("mascot.alt")} className="mx-auto h-auto w-28" />
      <h1 className="text-center text-3xl">{title}</h1>
      {children}
      <p className="text-center text-ink-soft">{footer}</p>
    </div>
  );
}

export function Field({ label, ...rest }: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="flex flex-col gap-1 text-sm font-extrabold text-ink-soft">
      {label}
      <input
        {...rest}
        className="rounded-2xl border-2 border-line bg-snow px-4 py-3 text-base font-bold text-ink focus:border-blue focus:bg-white"
      />
    </label>
  );
}
