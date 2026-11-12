"use client";
import { Card, Icon } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";

const BENEFITS = ["progress", "streak", "leagues", "mocks", "subjects"] as const;

/** Why to create a profile. */
export function RegisterBenefits() {
  const t = useT();
  return (
    <Card>
      <h2 className="mb-2 text-lg">{t("register.benefits.title")}</h2>
      <ul className="flex flex-col gap-2">
        {BENEFITS.map((b) => (
          <li key={b} className="flex items-start gap-2 font-bold">
            <Icon name="check" size={20} className="mt-0.5 text-brand" />
            {t(`register.benefit.${b}`)}
          </li>
        ))}
      </ul>
    </Card>
  );
}
