"use client";
import Link from "next/link";
import { buttonClass, Mascot } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";

export function FinalCta() {
  const t = useT();
  return (
    <section className="bg-green py-16 text-center text-white">
      <div className="mx-auto flex max-w-2xl flex-col items-center gap-5 px-4">
        <Mascot mood="celebrate" size={180} alt={t("mascot.alt")} className="h-auto w-40" />
        <h2 className="text-3xl">{t("landing.cta.title")}</h2>
        <Link href="/onboarding/" className={buttonClass("secondary", false, "border-white text-green-deep")}>
          {t("landing.hero.cta")}
        </Link>
      </div>
    </section>
  );
}
