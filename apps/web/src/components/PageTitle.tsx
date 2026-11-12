"use client";
import { useEffect, type ReactNode } from "react";
import { useT } from "@dtmai/i18n";

/** Sets the per-page document title for screens that render their own h1. */
export function useDocumentTitle(title: string) {
  const t = useT();
  useEffect(() => {
    document.title = `${title} · ${t("app.name")}`;
  }, [title, t]);
}

/** Page h1; also sets the per-page document title (static export has no per-route metadata for client pages). */
export function PageTitle({ children }: { children: ReactNode }) {
  const t = useT();
  useEffect(() => {
    if (typeof children === "string") document.title = `${children} · ${t("app.name")}`;
  }, [children, t]);
  return <h1 className="mb-6 text-3xl text-ink">{children}</h1>;
}
