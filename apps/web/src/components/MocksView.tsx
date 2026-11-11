"use client";
import { useState } from "react";
import { Button, Card } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { PageTitle } from "@/components/PageTitle";
import { ActiveAttemptCard } from "@/components/mocks/ActiveAttemptCard";
import { HistoryList } from "@/components/mocks/HistoryList";
import { MockCard } from "@/components/mocks/MockCard";
import { PersonalMockCard } from "@/components/mocks/PersonalMockCard";
import { PredictionCard } from "@/components/mocks/PredictionCard";
import { api, type Mock } from "@/lib/api";
import { pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";

const listMocks = () => api.unwrap(api.client.GET("/v1/assessment/mocks"));
const getActive = () => api.unwrap(api.client.GET("/v1/assessment/attempts/active"));
const PAGE = 10;
const KINDS = ["all", "official", "generated", "template"] as const;
const listBases = () => api.unwrap(api.client.GET("/v1/catalog/question-bases"));
// The API pages history by `limit` only (max 100), so "show more" grows it.
const getHistory = (limit: number) => api.unwrap(api.client.GET("/v1/assessment/attempts/history", { params: { query: { limit } } }));
const getPrediction = () => api.unwrap(api.client.GET("/v1/assessment/prediction"));

/** Each block loads independently so one failing endpoint does not blank the page. */
export function MocksView() {
  const t = useT();
  const { locale } = useLocale();
  const [kind, setKind] = useState<"all" | Mock["kind"]>("all");
  const [limit, setLimit] = useState(PAGE);
  const mocks = useAsync(listMocks, []);
  const bases = useAsync(listBases, []);
  const active = useAsync(getActive, []);
  const history = useAsync(() => getHistory(limit), [limit]);
  const prediction = useAsync(getPrediction, []);
  return (
    <>
      <PageTitle>{t("mocks.title")}</PageTitle>
      <div className="flex flex-col gap-8">
        {active.state.status === "ready" && active.state.data && <ActiveAttemptCard attempt={active.state.data} />}
        {prediction.state.status === "ready" && prediction.state.data.prediction && <PredictionCard view={prediction.state.data} />}

        <section aria-labelledby="mocks-list" className="flex flex-col gap-3">
          <h2 id="mocks-list" className="text-sm uppercase text-ink-soft">
            {t("mocks.previous")}
          </h2>
          <div role="group" aria-label={t("mocks.previous")} className="flex flex-wrap gap-2">
            {KINDS.map((k) => (
              <button
                key={k}
                type="button"
                aria-pressed={kind === k}
                onClick={() => setKind(k)}
                className={`rounded-xl border-2 px-3 py-1.5 font-bold ${kind === k ? "border-blue bg-blue text-white" : "border-line text-ink-soft"}`}
              >
                {k === "all" ? t("mocks.filterAll") : t(`mocks.kind.${k}`)}
              </button>
            ))}
          </div>
          <AsyncView state={mocks.state} onRetry={mocks.reload} isEmpty={(d) => d.length === 0} emptyText={t("mocks.empty")}>
            {(list) => {
              const shown = kind === "all" ? list : list.filter((m) => m.kind === kind);
              return (
                <div className="flex flex-col gap-3">
                  {shown.length === 0 && <p className="font-bold text-ink-soft">{t("mocks.empty")}</p>}
                  {shown.map((m) => (
                    <MockCard key={m.id} mock={m} />
                  ))}
                </div>
              );
            }}
          </AsyncView>
        </section>

        <section aria-labelledby="mocks-bases" className="flex flex-col gap-3">
          <h2 id="mocks-bases" className="text-sm uppercase text-ink-soft">
            {t("mocks.bases")}
          </h2>
          <AsyncView state={bases.state} onRetry={bases.reload} isEmpty={(d) => d.length === 0} emptyText={t("mocks.basesEmpty")}>
            {(list) => (
              <ul className="flex flex-col gap-2">
                {list.map((b) => (
                  <li key={b.id}>
                    <Card className="flex items-center justify-between gap-3 py-3">
                      <span className="font-bold">{pick(b.names, locale)}</span>
                      <span className="text-sm text-ink-soft">
                        {t(`mocks.baseKind.${b.kind}` as Parameters<typeof t>[0])}
                        {b.year ? ` · ${b.year}` : ""}
                      </span>
                    </Card>
                  </li>
                ))}
              </ul>
            )}
          </AsyncView>
        </section>

        <PersonalMockCard />

        <section aria-labelledby="mocks-history" className="flex flex-col gap-3">
          <h2 id="mocks-history" className="text-sm uppercase text-ink-soft">
            {t("mock.history")}
          </h2>
          <AsyncView state={history.state} onRetry={history.reload} isEmpty={(d) => d.length === 0} emptyText={t("mock.historyEmpty")}>
            {(items) => (
              <div className="flex flex-col gap-3">
                <HistoryList items={items} />
                {items.length >= limit && (
                  <Button variant="secondary" onClick={() => setLimit((n) => Math.min(n + PAGE, 100))} disabled={limit >= 100}>
                    {t("mock.historyMore")}
                  </Button>
                )}
              </div>
            )}
          </AsyncView>
        </section>
      </div>
    </>
  );
}
