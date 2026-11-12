"use client";
import { useEffect, useState } from "react";
import { ApiError } from "@dtmai/api-client";
import type * as TmaSdk from "@tma.js/sdk-react";
import { api } from "./api";
import { writeTokens } from "./session";

const sdk = (): Promise<typeof TmaSdk> => import("@tma.js/sdk-react");

let detected: Promise<boolean> | null = null;
let known = false;

/**
 * True when the page was launched by Telegram (launch params in the URL hash or the SDK's per-session cache).
 * Evaluated once per load and from any entry route, so deep links outside /tg are recognised too.
 */
export function detectTma(): Promise<boolean> {
  if (typeof window === "undefined") return Promise.resolve(false);
  detected ??= sdk()
    .then((s) => s.isTMA())
    .catch(() => false)
    .then((on) => (known = on));
  return detected;
}
// Capture launch params on the very first load, before client-side navigation drops the URL hash.
if (typeof window !== "undefined") void detectTma();

/** Payments are never offered inside the Mini App; this is derived from Telegram launch params, not from the route. */
export function useIsTma(): boolean {
  const [on, setOn] = useState(known);
  useEffect(() => {
    let live = true;
    void detectTma().then((v) => live && setOn(v));
    return () => {
      live = false;
    };
  }, []);
  return on;
}

/** Initialises the Mini App shell (ready, expand, theme, safe-area CSS vars). Returns raw initData or null outside Telegram. */
export async function setupTma(): Promise<string | null> {
  if (!(await detectTma())) return null;
  const s = await sdk();
  s.init();
  const initData = s.retrieveRawInitData() ?? null;
  try {
    if (s.miniApp.mount.isAvailable()) s.miniApp.mount();
    if (s.themeParams.mount.isAvailable()) s.themeParams.mount();
    if (s.viewport.mount.isAvailable()) await s.viewport.mount();
    if (s.viewport.bindCssVars.isAvailable()) s.viewport.bindCssVars();
    if (s.viewport.expand.isAvailable()) s.viewport.expand();
    if (s.miniApp.bindCssVars.isAvailable()) s.miniApp.bindCssVars();
    if (s.miniApp.ready.isAvailable()) s.miniApp.ready();
  } catch {
    /* optional chrome; auth still proceeds */
  }
  return initData;
}

/** Raw initData of this launch (null outside Telegram). */
export async function tmaInitData(): Promise<string | null> {
  if (!(await detectTma())) return null;
  try {
    return (await sdk()).retrieveRawInitData() ?? null;
  } catch {
    return null;
  }
}

/** Telegram `startapp` value of this launch, if any. */
export async function tmaStartParam(): Promise<string | null> {
  if (!(await detectTma())) return null;
  try {
    return (await sdk()).retrieveLaunchParams().tgWebAppStartParam ?? null;
  } catch {
    return null;
  }
}

const SECTIONS = ["learn", "practice", "mocks", "leagues", "quests", "profile", "lyceums"];
const UUID = "[0-9a-fA-F-]{36}";

/**
 * Maps a `startapp` value to an in-app route. Accepted: a section name (`mocks`, `leagues`, ...),
 * `run_<attemptId>`, `result_<attemptId>`. Anything else yields null (go to the default home).
 */
export function routeForStartParam(p: string | null): string | null {
  if (!p) return null;
  if (SECTIONS.includes(p)) return `/${p}/`;
  const m = new RegExp(`^(run|result)_(${UUID})$`).exec(p);
  return m ? `/mocks/${m[1]}/?attempt=${m[2]}` : null;
}

/** Re-authenticates with the launch initData and stores the new session. False when impossible or rejected. */
export async function reauthTma(): Promise<boolean> {
  const initData = await tmaInitData();
  if (!initData) return false;
  try {
    writeTokens(await api.unwrap(api.client.POST("/v1/identity/telegram/webapp", { body: { init_data: initData } })));
    return true;
  } catch {
    return false;
  }
}

/** Runs `fn`; on a 401 inside the Mini App re-authenticates with initData and retries once. */
export async function withTmaReauth<T>(fn: () => Promise<T>): Promise<T> {
  try {
    return await fn();
  } catch (e) {
    if (e instanceof ApiError && e.status === 401 && (await detectTma()) && (await reauthTma())) return fn();
    throw e;
  }
}

/** Shows the Telegram BackButton (inside the Mini App only) while `onBack` is set. */
export function useTmaBackButton(onBack: (() => void) | null) {
  const tma = useIsTma();
  useEffect(() => {
    if (!tma || !onBack) return;
    let off: (() => void) | undefined;
    let live = true;
    void sdk().then((s) => {
      if (!live || !s.backButton.show.isAvailable()) return;
      if (s.backButton.mount.isAvailable()) s.backButton.mount();
      s.backButton.show();
      off = s.backButton.onClick(onBack);
    });
    return () => {
      live = false;
      off?.();
      void sdk().then((s) => s.backButton.hide.isAvailable() && s.backButton.hide());
    };
  }, [tma, onBack]);
}
