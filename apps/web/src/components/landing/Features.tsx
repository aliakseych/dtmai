"use client";
import { Card, cn } from "@dtmai/ui";
import { useT, type MessageKey } from "@dtmai/i18n";
import { NavIcon } from "@/components/layout/NavIcon";

const FEATURES: { id: string; icon: string; tone: string }[] = [
  { id: "path", icon: "learn", tone: "bg-green" },
  { id: "mocks", icon: "mocks", tone: "bg-blue" },
  { id: "personal", icon: "practice", tone: "bg-orange" },
  { id: "ai", icon: "premium", tone: "bg-brand" },
  { id: "leagues", icon: "leagues", tone: "bg-gold" },
  { id: "lyceums", icon: "lyceums", tone: "bg-red" },
];

export function Features() {
  const t = useT();
  return (
    <section id="features" className="mx-auto max-w-6xl px-4 py-16">
      <h2 className="mb-10 text-center text-3xl">{t("landing.features.title")}</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f) => (
          <Card key={f.id} className="flex flex-col gap-3">
            <span className={cn("grid h-14 w-14 place-items-center rounded-2xl text-white", f.tone)}>
              <NavIcon name={f.icon} />
            </span>
            <h3 className="text-xl">{t(`landing.features.${f.id}.title` as MessageKey)}</h3>
            <p className="text-ink-soft">{t(`landing.features.${f.id}.text` as MessageKey)}</p>
          </Card>
        ))}
      </div>
    </section>
  );
}
