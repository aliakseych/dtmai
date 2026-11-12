"use client";
import { Badge, Icon } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";

export function VerifiedBadge() {
  const t = useT();
  return (
    <Badge tone="accent">
      <Icon name="check" size={16} />
      {t("lyceums.verified")}
    </Badge>
  );
}
