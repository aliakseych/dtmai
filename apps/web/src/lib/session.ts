import type { Tokens } from "@dtmai/api-client";

const KEY = "dtmai.tokens";
export type StoredTokens = Pick<Tokens, "access_token" | "refresh_token">;

export function readTokens(): StoredTokens | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as StoredTokens) : null;
  } catch {
    return null;
  }
}

export function writeTokens(t: StoredTokens | null) {
  if (t) localStorage.setItem(KEY, JSON.stringify({ access_token: t.access_token, refresh_token: t.refresh_token }));
  else localStorage.removeItem(KEY);
}
