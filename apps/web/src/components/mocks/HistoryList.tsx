"use client";
import Link from "next/link";
import { Card } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
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
            <span className="text-ink-soft">{new Date(h.submitted_at ?? h.started_at).toLocaleDateString(locale)}</span>
            <span className="font-extrabold">{t("mock.score", { score: num.format(h.score), max: num.format(h.max_total) })}</span>
            <Link href={`/mocks/result/?attempt=${h.attempt_id}`} className="font-bold text-blue-deep underline">
              {t("mock.view")}
            </Link>
          </Card>
        </li>
      ))}
    </ul>
  );
}
