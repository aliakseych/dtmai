"use client";
import { useState } from "react";
import { Avatar, Button, Card, GemsStat, HeartsStat, StreakFlame, XpStat, useToast, Icon } from "@dtmai/ui";
import { LocaleSwitcher, useT } from "@dtmai/i18n";
import Link from "next/link";
import { buttonClass } from "@dtmai/ui";
import { AsyncView } from "@/components/AsyncView";
import { GoalRing } from "@/components/GoalRing";
import { PageTitle } from "@/components/PageTitle";
import { StatsSection } from "@/components/profile/StatsSection";
import { Reveal } from "@/components/motion/Reveal";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { sharedBillingMe, useBilling } from "@/lib/billing";
import { useStats } from "@/lib/stats";
import { useAsync } from "@/lib/useAsync";

const GOALS = [10, 20, 30, 50] as const;

export function ProfileView() {
  const t = useT();
  const toast = useToast();
  const { me, isGuest, logout } = useAuth();
  const { canBuy } = useBilling();
  const { state, reload } = useStats();
  const billing = useAsync(() => (isGuest || !me ? Promise.resolve(null) : sharedBillingMe(me.id)), [isGuest, me?.id]);

  async function setGoal(xp: (typeof GOALS)[number]) {
    try {
      await api.unwrap(api.client.PUT("/v1/me/daily-goal", { body: { xp } }));
      reload();
    } catch {
      toast(t("common.error"), "error");
    }
  }
  const [buying, setBuying] = useState(false);
  async function buyFreeze() {
    setBuying(true);
    try {
      await api.unwrap(api.client.POST("/v1/gamification/streak/freeze"));
      toast(t("streak.freeze.bought"), "success");
      reload();
    } catch {
      toast(t("streak.freeze.failed"), "error");
    } finally {
      setBuying(false);
    }
  }
  const plan = billing.state.status === "ready" ? billing.state.data : null;
  const premium = !!plan && plan.entitlements.plan_code !== "free";

  return (
    <>
      <PageTitle>{t("profile.title")}</PageTitle>
      <AsyncView state={state} onRetry={reload}>
        {(s) => (
          <div className="mx-auto flex w-full min-w-0 max-w-5xl flex-col gap-4">
            <Reveal y={12}>
              <Card className="flex items-center gap-4 bg-brand-soft">
                <Avatar name={me?.name ?? "?"} size={72} />
                <div className="min-w-0 flex-1">
                  <h2 className="break-words text-2xl">{isGuest ? t("profile.guest") : me?.name}</h2>
                  {me?.email && <p className="break-all text-ink-soft">{me.email}</p>}
                </div>
                <StreakFlame days={s.streak} />
              </Card>
            </Reveal>
            {isGuest && (
              <Card className="flex flex-col gap-2">
                <p className="text-ink">{t("guest.banner")}</p>
                <Link href="/register/" className={buttonClass("primary", true)}>
                  {t("guest.save")}
                </Link>
              </Card>
            )}
            <StatsSection />
            <Card className="flex flex-wrap justify-around gap-4">
              <XpStat value={s.xp_total} label={t("stat.xp")} />
              <GemsStat value={s.gems} label={t("stat.gems")} />
              <HeartsStat value={s.hearts.unlimited ? "∞" : `${s.hearts.count}/${s.hearts.max}`} label={t("stat.hearts")} />
            </Card>
            <Card className="flex flex-col gap-3">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-xl">{t("stat.streak")}</h2>
                <StreakFlame days={s.streak} />
              </div>
              <p className={s.streak_at_risk ? "font-bold text-red" : "text-ink-soft"}>
                {s.streak_at_risk ? t("streak.atRisk") : s.streak_active_today ? t("streak.doneToday") : s.streak > 0 ? t("streak.longest", { n: s.streak_longest }) : t("streak.practice")}
              </p>
              <div className="flex items-center justify-between gap-3">
                <span className="flex items-center gap-2 font-bold text-ink">
                  <Icon name="snowflake" size={20} className="text-brand" />
                  {t("streak.freezes", { n: s.streak_freezes })}
                </span>
                {!isGuest && (
                  <Button variant="secondary" disabled={buying || s.gems < s.freeze_cost_gems} onClick={() => void buyFreeze()}>
                    {t("streak.freeze.buyFor", { n: s.freeze_cost_gems })}
                  </Button>
                )}
              </div>
            </Card>
            <Card className="flex flex-col gap-3">
              <div className="flex items-center gap-4">
                <GoalRing done={s.today_xp} goal={s.daily_goal_xp} />
                <h2 className="text-xl">{t("goal.title")}</h2>
              </div>
              <div role="radiogroup" aria-label={t("goal.pick")} className="grid grid-cols-4 gap-2">
                {GOALS.map((g) => (
                  <button
                    key={g}
                    type="button"
                    role="radio"
                    aria-checked={s.daily_goal_xp === g}
                    onClick={() => void setGoal(g)}
                    className={`rounded-2xl border-2 px-2 py-3 font-extrabold ${s.daily_goal_xp === g ? "border-brand bg-brand-soft text-brand" : "border-line text-ink"}`}
                  >
                    {g} {t("stat.xp")}
                  </button>
                ))}
              </div>
            </Card>
            <Card className="flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg">{t("profile.plan")}</h2>
                <p className="text-ink-soft">{premium ? t("premium.active") : t("plan.free.name")}</p>
              </div>
              {canBuy && (
                <Link href="/premium/" className={buttonClass("super")}>
                  {t("plan.premium.cta")}
                </Link>
              )}
            </Card>
            {!isGuest && (
              <Card className="flex flex-col gap-3">
                <h2 className="text-lg">{t("profile.account")}</h2>
                <NameEditor />
                <Link href="/plan/setup/" className={buttonClass("secondary", true)}>
                  {t("profile.reminders")}
                </Link>
                <Link href="/forgot/" className={buttonClass("secondary", true)}>
                  {t("profile.changePassword")}
                </Link>
              </Card>
            )}
            <Card className="flex items-center justify-between">
              <span className="text-lg">{t("common.language")}</span>
              <LocaleSwitcher />
            </Card>
            <Button
              variant="danger"
              block
              onClick={async () => {
                await logout();
              }}
            >
              {t("profile.logout")}
            </Button>
          </div>
        )}
      </AsyncView>
    </>
  );
}

function NameEditor() {
  const t = useT();
  const toast = useToast();
  const { me, reloadMe } = useAuth();
  const [name, setName] = useState(me?.name ?? "");
  const [busy, setBusy] = useState(false);
  const dirty = name.trim().length > 0 && name.trim() !== me?.name;
  async function save() {
    setBusy(true);
    try {
      await api.unwrap(api.client.PATCH("/v1/identity/me", { body: { name: name.trim() } }));
      await reloadMe();
      toast(t("profile.saved"), "success");
    } catch {
      toast(t("common.error"), "error");
    } finally {
      setBusy(false);
    }
  }
  return (
    <form
      className="flex flex-wrap items-end gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        if (dirty) void save();
      }}
    >
      <label className="flex min-w-0 flex-1 flex-col gap-1">
        <span className="text-sm font-bold uppercase text-ink-soft">{t("profile.name")}</span>
        <input value={name} maxLength={80} onChange={(e) => setName(e.target.value)} className="rounded-2xl border-2 border-line bg-white px-4 py-3 font-extrabold" />
      </label>
      <Button type="submit" disabled={!dirty || busy}>
        {t("profile.save")}
      </Button>
    </form>
  );
}
