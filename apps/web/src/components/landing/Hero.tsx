"use client";
import Link from "next/link";
import { buttonClass, Mascot } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { Float, Reveal } from "@/components/motion/Reveal";

export function Hero() {
  const t = useT();
  return (
    <section className="bg-brand text-white">
      <div className="mx-auto grid max-w-6xl items-center gap-8 px-4 py-12 md:grid-cols-2 md:py-20">
        <Reveal className="flex flex-col items-center gap-6 text-center md:items-start md:text-left">
          <h1 className="text-4xl leading-tight md:text-5xl">{t("landing.hero.title")}</h1>
          <p className="max-w-lg text-lg font-bold text-white/85">{t("landing.hero.subtitle")}</p>
          <div className="flex w-full max-w-xs flex-col gap-3">
            <Link href="/onboarding/" className={buttonClass("super", true)}>
              {t("landing.hero.cta")}
            </Link>
            <Link href="/login/" className={buttonClass("secondary", true)}>
              {t("landing.hero.haveAccount")}
            </Link>
          </div>
        </Reveal>
        <Float className="flex justify-center">
          <Mascot mood="wave" size={360} alt={t("mascot.alt")} className="h-auto w-56 md:w-[360px]" />
        </Float>
      </div>
    </section>
  );
}
