"use client";
import { useT } from "@dtmai/i18n";

export function OrDivider() {
  const t = useT();
  return (
    <div className="flex items-center gap-3 text-sm font-extrabold uppercase text-ink-soft">
      <span className="h-0.5 flex-1 bg-line" />
      {t("auth.or")}
      <span className="h-0.5 flex-1 bg-line" />
    </div>
  );
}
