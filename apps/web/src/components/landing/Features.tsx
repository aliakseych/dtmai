"use client";
import { Card, cn, Icon, type IconName } from "@dtmai/ui";
import { useT, type MessageKey } from "@dtmai/i18n";
import { Reveal } from "@/components/motion/Reveal";

const FEATURES: { id: string; icon: IconName; tone: string }[] = [
  { id: "path", icon: "learn", tone: "bg-brand text-white" },
  { id: "mocks", icon: "mocks", tone: "bg-accent text-ink" },
  { id: "personal", icon: "practice", tone: "bg-ink text-white" },
  { id: "ai", icon: "premium", tone: "bg-brand text-white" },
  { id: "leagues", icon: "leagues", tone: "bg-accent text-ink" },
  { id: "lyceums", icon: "lyceums", tone: "bg-ink text-white" },
];

export function Features() {
  const t = useT();
  return (
    <section id="features" className="mx-auto max-w-6xl px-4 py-16">
      <h2 className="mb-10 text-center text-3xl">{t("landing.features.title")}</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f, i) => (
          <Reveal key={f.id} delay={(i % 3) * 0.08}>
            <Card className="flex h-full flex-col gap-3">
              <span className={cn("grid h-14 w-14 place-items-center rounded-2xl", f.tone)}>
                <Icon name={f.icon} size={28} />
              </span>
              <h3 className="text-xl">{t(`landing.features.${f.id}.title` as MessageKey)}</h3>
              <p className="text-ink-soft">{t(`landing.features.${f.id}.text` as MessageKey)}</p>
            </Card>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
