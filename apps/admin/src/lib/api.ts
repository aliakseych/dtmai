import { createApiClient } from "@dtmai/api-client";
import { apiUrl } from "./env";
import { readTokens, writeTokens } from "./session";

let onUnauthorized: () => void = () => {};
export const setUnauthorizedHandler = (fn: () => void) => (onUnauthorized = fn);

/** Single app-wide client: bearer from session, refresh rotation, `Accept-Language: en`. */
export const api = createApiClient({
  baseUrl: typeof window === "undefined" ? "" : apiUrl(),
  getToken: () => readTokens()?.access_token,
  getRefreshToken: () => readTokens()?.refresh_token,
  setTokens: writeTokens,
  onUnauthorized: () => onUnauthorized(),
  locale: "en",
});

/** Lazily rebuilt so runtime env.js is honoured (script runs before hydration; module may load earlier on SSR). */
export type Api = typeof api;
