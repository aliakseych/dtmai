"use client";
import Link from "next/link";
import { buttonClass, Card } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { clock, useCountdown } from "@/lib/useCountdown";
import type { Attempt } from "@/lib/api";

export function ActiveAttemptCard({ attempt }: { attempt: Attempt }) {
  const t = useT();
  const left = useCountdown(attempt.deadline);
  return (
    <Card className="flex flex-wrap items-center justify-between gap-3 border-brand bg-brand-soft">
      <div>
        <h2 className="text-lg">{t("mock.resume")}</h2>
        <p className="font-bold text-ink-soft">{t("mock.timeLeft", { time: clock(left) })}</p>
      </div>
      <Link href={`/mocks/run/?attempt=${attempt.id}`} className={buttonClass("primary")}>
        {t("mock.resumeBtn")}
      </Link>
    </Card>
  );
}
