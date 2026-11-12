"use client";
import Link from "next/link";
import { buttonClass, Mascot } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { useDocumentTitle } from "@/components/PageTitle";

export default function NotFound() {
  const t = useT();
  useDocumentTitle(t("err.notFound.title"));
  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-3 p-4 text-center">
      <Mascot mood="sad" size={120} alt="" />
      <h1 className="text-2xl">{t("err.notFound.title")}</h1>
      <p className="max-w-sm text-ink-soft">{t("err.notFound.body")}</p>
      <Link href="/" className={buttonClass("primary")}>
        {t("nav.home")}
      </Link>
    </main>
  );
}
