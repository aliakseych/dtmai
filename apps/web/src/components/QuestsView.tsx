"use client";
import { useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { PageTitle } from "@/components/PageTitle";
import { QuestItem } from "@/components/quests/QuestItem";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";

/** Quests complete and pay out automatically when the target is reached; there is no claim step. */
export function QuestsView() {
  const t = useT();
  const { state, reload } = useAsync(() => api.unwrap(api.client.GET("/v1/gamification/quests")), []);
  return (
    <>
      <PageTitle>{t("quests.title")}</PageTitle>
      <AsyncView state={state} onRetry={reload} isEmpty={(d) => d.length === 0} emptyText={t("quests.empty")}>
        {(quests) => (
          <ul className="flex flex-col gap-3">
            {quests.map((q) => (
              <QuestItem key={q.id} quest={q} />
            ))}
          </ul>
        )}
      </AsyncView>
    </>
  );
}
