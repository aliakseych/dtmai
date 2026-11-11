"use client";
import { useT } from "@dtmai/i18n";

export function VerifiedBadge() {
  const t = useT();
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-accent px-2 py-0.5 text-xs font-extrabold text-black">
      <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 8.5 6.5 12 13 4.5" />
      </svg>
      {t("lyceums.verified")}
    </span>
  );
}
