"use client";
import { Card, GemsStat, ProgressBar, XpStat } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { PageTitle } from "@/components/PageTitle";
import { api } from "@/lib/api";
import { pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";

/** Quests complete and pay out automatically when the target is reached; there is no claim step. */
export function QuestsView() {
  const t = useT();
  const { locale } = useLocale();
  const { state, reload } = useAsync(() => api.unwrap(api.client.GET("/v1/gamification/quests")), []);
  return (
    <>
      <PageTitle>{t("quests.title")}</PageTitle>
      <AsyncView state={state} onRetry={reload} isEmpty={(d) => d.length === 0} emptyText={t("quests.empty")}>
        {(quests) => (
          <ul className="flex flex-col gap-3">
            {quests.map((q) => {
              const title = pick(q.title, locale);
              return (
                <Card key={q.id} className="flex items-center gap-4">
                  <div className="flex flex-1 flex-col gap-2">
                    <h2 className="text-lg">{title}</h2>
                    <ProgressBar value={Math.min(q.progress, q.target)} max={q.target} color="bg-gold" label={title} />
                    <div className="flex gap-4">
                      <GemsStat value={`+${q.reward_gems}`} label={t("stat.gems")} />
                      {q.reward_xp > 0 && <XpStat value={`+${q.reward_xp}`} label={t("stat.xp")} />}
                    </div>
                  </div>
                  {q.completed && <span className="rounded-full bg-green-soft px-3 py-1 text-sm font-extrabold text-[#2f6200]">✓ {t("quests.done")}</span>}
                </Card>
              );
            })}
          </ul>
        )}
      </AsyncView>
    </>
  );
}
