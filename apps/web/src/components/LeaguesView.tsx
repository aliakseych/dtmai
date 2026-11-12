"use client";
import { useState } from "react";
import { Avatar, Button, Card, cn, LeagueBadge, Tabs, useToast } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { PageTitle } from "@/components/PageTitle";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";

const ZONE = { promote: "bg-brand-soft", demote: "bg-red-soft", safe: "" } as const;

function LeagueTab() {
  const t = useT();
  const { locale } = useLocale();
  const { state, reload } = useAsync(() => api.unwrap(api.client.GET("/v1/gamification/leagues/current")), []);
  return (
    <AsyncView state={state} onRetry={reload} isEmpty={(d) => !d || d.rows.length === 0}>
      {(l) => {
        if (!l) return null;
        const days = Math.max(0, Math.ceil((new Date(l.ends_at).getTime() - Date.now()) / 86_400_000));
        const name = pick(l.tier.name, locale);
        return (
          <>
            <div className="mb-6 flex flex-col items-center gap-4 text-center">
              <LeagueBadge tier={l.tier.idx} name={name} size={88} />
              <h2 className="text-3xl">{name}</h2>
              <p className="text-ink-soft">
                {t("leagues.promo", { n: l.tier.promote_count })} · {t("leagues.endsIn", { n: days })}
              </p>
            </div>
            <Card pad="none" className="">
              <ol>
                {l.rows.map((e) => (
                  <li
                    key={e.user_id}
                    aria-current={e.is_me ? "true" : undefined}
                    className={cn("flex min-w-0 items-center gap-4 border-b-2 border-line px-4 py-3 last:border-b-0", ZONE[e.zone], e.is_me && "ring-2 ring-inset ring-brand")}
                  >
                    <span className="w-6 text-center font-extrabold">{e.rank}</span>
                    <Avatar name={e.name} size={44} />
                    <span className="min-w-0 flex-1 truncate text-ink">
                      {e.name}
                      {e.zone !== "safe" && <span className="ml-2 text-xs font-extrabold uppercase">{t(e.zone === "promote" ? "leagues.zone.promote" : "leagues.zone.demote")}</span>}
                    </span>
                    <span className="shrink-0 text-ink-soft">
                      {e.xp} {t("stat.xp")}
                    </span>
                  </li>
                ))}
              </ol>
            </Card>
          </>
        );
      }}
    </AsyncView>
  );
}

type Row = { user_id: string; name: string; xp: number };
type Period = "week" | "all";

function Board({ kind }: { kind: "friends" | "lyceum" }) {
  const t = useT();
  const toast = useToast();
  const { me } = useAuth();
  const [period, setPeriod] = useState<Period>("week");
  const board = useAsync(
    () =>
      kind === "friends"
        ? api.unwrap(api.client.GET("/v1/gamification/leaderboard/friends", { params: { query: { period } } }))
        : api.unwrap(api.client.GET("/v1/gamification/leaderboard/lyceum", { params: { query: { period, limit: 50 } } })),
    [kind, period],
  );
  const friends = useAsync(() => api.unwrap(api.client.GET("/v1/gamification/friends")), []);
  const followed = new Set<string>(friends.state.status === "ready" ? (friends.state.data as Row[]).map((f) => f.user_id) : []);

  async function toggle(id: string, on: boolean) {
    try {
      await api.unwrap(
        on
          ? api.client.DELETE("/v1/gamification/friends/{user_id}", { params: { path: { user_id: id } } })
          : api.client.POST("/v1/gamification/friends/{user_id}", { params: { path: { user_id: id } } }),
      );
      friends.reload();
      if (kind === "friends") board.reload();
    } catch {
      toast(t("common.error"), "error");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <Tabs
        items={[
          { id: "week" as Period, label: t("leagues.period.week") },
          { id: "all" as Period, label: t("leagues.period.all") },
        ]}
        value={period}
        onChange={setPeriod}
      />
      <AsyncView
        state={board.state}
        onRetry={board.reload}
        isEmpty={(d) => d.rows.length === 0}
        emptyText={kind === "friends" ? t("leagues.friends.empty") : t("leagues.lyceum.empty")}
      >
        {(b) => (
          <Card pad="none" className="">
            <ol>
              {b.rows.map((e, i) => {
                const mine = e.user_id === me?.id;
                const on = followed.has(e.user_id);
                return (
                  <li
                    key={e.user_id}
                    aria-current={mine ? "true" : undefined}
                    className={cn("flex items-center gap-3 border-b-2 border-line px-4 py-3 last:border-b-0", mine && "ring-2 ring-inset ring-brand")}
                  >
                    <span className="w-6 text-center font-extrabold">{i + 1}</span>
                    <Avatar name={e.name} size={44} />
                    <span className="min-w-0 flex-1 truncate text-ink">{e.name}</span>
                    <span className="shrink-0 text-ink-soft">
                      {e.xp} {t("stat.xp")}
                    </span>
                    {!mine && (
                      <Button variant={on ? "secondary" : "primary"} onClick={() => void toggle(e.user_id, on)}>
                        {on ? t("leagues.friend.remove") : t("leagues.friend.add")}
                      </Button>
                    )}
                  </li>
                );
              })}
            </ol>
          </Card>
        )}
      </AsyncView>
    </div>
  );
}

type Tab = "league" | "friends" | "lyceum";

export function LeaguesView() {
  const t = useT();
  const [tab, setTab] = useState<Tab>("league");
  return (
    <div className="flex min-w-0 flex-col gap-6">
      <PageTitle>{t("nav.leagues")}</PageTitle>
      <Tabs
        items={[
          { id: "league" as Tab, label: t("leagues.tab.league") },
          { id: "friends" as Tab, label: t("leagues.tab.friends") },
          { id: "lyceum" as Tab, label: t("leagues.tab.lyceum") },
        ]}
        value={tab}
        onChange={setTab}
        className="max-w-full"
      />
      {tab === "league" ? <LeagueTab /> : <Board key={tab} kind={tab} />}
    </div>
  );
}
