"use client";
import { useT, type MessageKey } from "@dtmai/i18n";

export function Faq() {
  const t = useT();
  return (
    <section id="faq" className="mx-auto max-w-3xl px-4 py-16">
      <h2 className="mb-8 text-center text-3xl">{t("landing.faq.title")}</h2>
      <div className="flex flex-col gap-3">
        {[1, 2, 3, 4].map((n) => (
          <details key={n} className="group rounded-card border-2 border-line p-4">
            <summary className="cursor-pointer text-lg font-extrabold text-ink">{t(`landing.faq.${n}.q` as MessageKey)}</summary>
            <p className="mt-2 text-ink-soft">{t(`landing.faq.${n}.a` as MessageKey)}</p>
          </details>
        ))}
      </div>
    </section>
  );
}
