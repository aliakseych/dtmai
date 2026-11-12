import { createApiClient } from "@dtmai/api-client";
import { apiUrl } from "./env";
import { readTokens, writeTokens } from "./session";

import { LOCALES } from "@dtmai/i18n";

/** UI locale as persisted by the @dtmai/i18n switcher (`dtmai.locale`); read per request so a switch applies immediately. */
export function currentLocale(): string {
  if (typeof window === "undefined") return "en";
  try {
    const v = window.localStorage.getItem("dtmai.locale");
    return v && (LOCALES as readonly string[]).includes(v) ? v : "en";
  } catch { return "en"; }
}

let onUnauthorized: () => void = () => {};
export const setUnauthorizedHandler = (fn: () => void) => (onUnauthorized = fn);

/** Single app-wide client: bearer from session, refresh rotation, `Accept-Language: en`. */
export const api = createApiClient({
  baseUrl: typeof window === "undefined" ? "" : apiUrl(),
  getToken: () => readTokens()?.access_token,
  getRefreshToken: () => readTokens()?.refresh_token,
  setTokens: writeTokens,
  onUnauthorized: () => onUnauthorized(),
  locale: () => currentLocale(),
});

/** Lazily rebuilt so runtime env.js is honoured (script runs before hydration; module may load earlier on SSR). */
export type Api = typeof api;
