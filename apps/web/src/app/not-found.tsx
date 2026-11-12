"use client";
import Link from "next/link";
import { buttonClass, EmptyState } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";

export default function NotFound() {
  const t = useT();
  return (
    <main className="mx-auto flex min-h-dvh max-w-md items-center p-4">
      <EmptyState
        mood="sad"
        title={t("err.notFound.title")}
        body={t("err.notFound.body")}
        action={
          <Link href="/" className={buttonClass("primary")}>
            {t("nav.home")}
          </Link>
        }
      />
    </main>
  );
}
