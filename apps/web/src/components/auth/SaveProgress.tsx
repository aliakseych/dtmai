"use client";
import Link from "next/link";
import { buttonClass, Card } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { GoogleSignIn } from "./GoogleSignIn";

/** Shown to guests once their plan exists: only now do we ask for an account (email or Google). */
export function SaveProgress() {
  const t = useT();
  return (
    <Card className="mb-5 flex flex-col items-center gap-3 text-center">
      <h2 className="text-xl">{t("auth.save.title")}</h2>
      <p className="text-ink-soft">{t("auth.save.plan")}</p>
      <GoogleSignIn />
      <Link href="/register/" className={buttonClass("primary", true, "min-h-11")}>
        {t("auth.save.email")}
      </Link>
    </Card>
  );
}
