"use client";
import Link from "next/link";
import { Card } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { formatDateTime } from "@/lib/planDates";
import { fmt } from "@/lib/localized";
import type { HistoryItem } from "@/lib/api";

export function HistoryList({ items }: { items: HistoryItem[] }) {
  const t = useT();
  const { locale } = useLocale();
  const num = fmt(locale);
  return (
    <ul className="flex flex-col gap-2">
      {items.map((h) => (
        <li key={h.attempt_id}>
          <Card className="flex items-center justify-between gap-3 py-3">
            <span className="flex flex-col">
              <span className="text-ink-soft">{formatDateTime(h.submitted_at ?? h.started_at, locale)}</span>
              {h.kind === "personal" && <span className="text-sm font-bold text-ink-soft">{t("mock.personal")}</span>}
            </span>
            <span className="font-extrabold">{t("mock.score", { score: num.format(h.correct), max: num.format(h.questions || h.correct) })}</span>
            <Link href={`/mocks/result/?attempt=${h.attempt_id}`} className="inline-flex min-h-11 items-center font-bold text-brand underline">
              {t("mock.view")}
            </Link>
          </Card>
        </li>
      ))}
    </ul>
  );
}
