"use client";
import { Mascot } from "@dtmai/ui";
import { useT, type MessageKey } from "@dtmai/i18n";

export function Faq() {
  const t = useT();
  return (
    <section id="faq" className="scroll-mt-20 mx-auto max-w-3xl px-4 py-16">
      <Mascot mood="question" size={120} alt="" className="mx-auto mb-3 h-auto w-24" />
      <h2 className="mb-8 text-center text-3xl">{t("landing.faq.title")}</h2>
      <div className="flex flex-col gap-3">
        {[1, 2, 3, 4].map((n) => (
          <details key={n} className="group rounded-card border-2 border-line bg-white p-4">
            <summary className="flex min-h-11 cursor-pointer list-none items-center text-lg [&::-webkit-details-marker]:hidden font-extrabold text-ink">{t(`landing.faq.${n}.q` as MessageKey)}</summary>
            <p className="mt-2 text-ink-soft">{t(`landing.faq.${n}.a` as MessageKey)}</p>
          </details>
        ))}
      </div>
    </section>
  );
}
