"use client";
import { useEffect, useState } from "react";
import { api } from "./api";
import { useAuth } from "./auth";
import { useIsTma } from "./tma";

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
    api
      .unwrap(api.client.GET("/v1/billing/config"))
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
    api
      .unwrap(api.client.GET("/v1/billing/me"))
      .then((b) => live && setPremium(b.entitlements.plan_code !== "free"))
      .catch(() => live && setPremium(false));
    return () => {
      live = false;
    };
  }, [me]);
  return { paymentsEnabled, premium, tma, loaded, canBuy: paymentsEnabled && !premium && !tma };
}
