"use client";
import Link from "next/link";
import { buttonClass, Mascot } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { Float, Reveal } from "@/components/motion/Reveal";

export function FinalCta() {
  const t = useT();
  return (
    <section className="bg-brand py-16 text-center text-white">
      <Reveal className="mx-auto flex max-w-2xl flex-col items-center gap-5 px-4">
        <Float>
          <Mascot mood="celebrate" size={180} alt={t("mascot.alt")} className="h-auto w-40" />
        </Float>
        <h2 className="text-3xl">{t("landing.cta.title")}</h2>
        <Link href="/onboarding/" className={buttonClass("super", false)}>
          {t("landing.hero.cta")}
        </Link>
      </Reveal>
    </section>
  );
}
