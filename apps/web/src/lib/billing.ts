"use client";
import { useEffect, useState } from "react";
import { api } from "./api";
import { useAuth } from "./auth";
import { useIsTma } from "./tma";

const TTL_MS = 30_000;
const configCache: { p?: ReturnType<typeof loadConfig> } = {};
const meCache = new Map<string, { at: number; p: ReturnType<typeof loadMe> }>();

function loadConfig() {
  return api.unwrap(api.client.GET("/v1/billing/config"));
}
function loadMe() {
  return api.unwrap(api.client.GET("/v1/billing/me"));
}

/** One config request per page load; shared by every `useBilling` caller. */
export function sharedBillingConfig() {
  const p = (configCache.p ??= loadConfig());
  p.catch(() => {
    if (configCache.p === p) configCache.p = undefined;
  });
  return p;
}

/** One subscription request per user within 30 s; shared by every caller (ProfileView included). */
export function sharedBillingMe(userId: string) {
  const hit = meCache.get(userId);
  if (hit && Date.now() - hit.at < TTL_MS) return hit.p;
  meCache.clear();
  const p = loadMe();
  meCache.set(userId, { at: Date.now(), p });
  p.catch(() => meCache.delete(userId));
  return p;
}

/**
 * Payment visibility. `payments_enabled` comes from the API; the buy CTA is shown only
 * on the web, never inside the Telegram Mini App, and never to a user who is already premium.
 */
export function useBilling() {
  const { me } = useAuth();
  const tma = useIsTma();
  const [paymentsEnabled, setEnabled] = useState(false);
  const [premium, setPremium] = useState(false);
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    let live = true;
    sharedBillingConfig()
      .then((c) => live && setEnabled(c.payments_enabled))
      .catch(() => live && setEnabled(false))
      .finally(() => live && setLoaded(true));
    return () => {
      live = false;
    };
  }, []);
  useEffect(() => {
    if (!me || me.roles.includes("guest")) return setPremium(false);
    let live = true;
    sharedBillingMe(me.id)
      .then((b) => live && setPremium(b.entitlements.plan_code !== "free"))
      .catch(() => live && setPremium(false));
    return () => {
      live = false;
    };
  }, [me]);
  return { paymentsEnabled, premium, tma, loaded, canBuy: paymentsEnabled && !premium && !tma };
}
