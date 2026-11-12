"use client";
import { Card } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { Reveal } from "@/components/motion/Reveal";

export function HowItWorks() {
  const t = useT();
  const steps = [
    { title: t("landing.how.1.title"), text: t("landing.how.1.text") },
    { title: t("landing.how.2.title"), text: t("landing.how.2.text") },
    { title: t("landing.how.3.title"), text: t("landing.how.3.text") },
  ];
  return (
    <section className="bg-snow py-16">
      <div className="mx-auto max-w-6xl px-4">
        <h2 className="mb-10 text-center text-3xl">{t("landing.how.title")}</h2>
        <ol className="grid gap-4 md:grid-cols-3">
          {steps.map((s, i) => (
            <li key={s.title}>
              <Reveal delay={i * 0.08} className="h-full">
                <Card className="h-full">
                  <span className="mb-3 grid h-10 w-10 place-items-center rounded-full bg-accent text-lg font-extrabold text-ink">{i + 1}</span>
                  <h3 className="mb-1 text-xl">{s.title}</h3>
                  <p className="text-ink-soft">{s.text}</p>
                </Card>
              </Reveal>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
