"use client";
import Link from "next/link";
import { Card, Skeleton } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { QuestItem } from "@/components/quests/QuestItem";

/** Today's quests in the right rail; hidden when the call fails or there are none. */
export function QuestsPanel() {
  const t = useT();
  const { state } = useAsync(() => api.unwrap(api.client.GET("/v1/gamification/quests")), []);
  if (state.status === "error") return null;
  if (state.status === "ready" && state.data.length === 0) return null;
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-lg">{t("nav.quests")}</h2>
        <Link href="/quests/" className="text-sm font-extrabold uppercase text-brand hover:underline">
          {t("quests.all")}
        </Link>
      </div>
      {state.status === "ready" ? (
        <ul className="flex flex-col gap-2">
          {state.data.map((q) => (
            <QuestItem key={q.id} quest={q} compact />
          ))}
        </ul>
      ) : (
        <Skeleton className="h-20 w-full" />
      )}
    </Card>
  );
}
