"use client";
import Link from "next/link";
import { buttonClass, Mascot } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";

export function Hero() {
  const t = useT();
  return (
    <section className="mx-auto grid max-w-6xl items-center gap-8 px-4 py-12 md:grid-cols-2 md:py-20">
      <div className="flex flex-col items-center gap-6 text-center md:items-start md:text-left">
        <h1 className="text-4xl leading-tight text-ink md:text-5xl">{t("landing.hero.title")}</h1>
        <p className="max-w-lg text-lg text-ink-soft">{t("landing.hero.subtitle")}</p>
        <div className="flex w-full max-w-xs flex-col gap-3">
          <Link href="/onboarding/" className={buttonClass("primary", true)}>
            {t("landing.hero.cta")}
          </Link>
          <Link href="/login/" className={buttonClass("secondary", true)}>
            {t("landing.hero.haveAccount")}
          </Link>
        </div>
      </div>
      <div className="flex justify-center">
        <Mascot mood="wave" size={360} alt={t("mascot.alt")} className="h-auto w-56 md:w-[360px]" />
      </div>
    </section>
  );
}
