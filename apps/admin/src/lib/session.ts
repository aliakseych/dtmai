import type { Tokens } from "@dtmai/api-client";

const KEY = "dtmai.admin.tokens";

export function readTokens(): Pick<Tokens, "access_token" | "refresh_token"> | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}
export function writeTokens(t: Pick<Tokens, "access_token" | "refresh_token"> | null) {
  if (t) localStorage.setItem(KEY, JSON.stringify({ access_token: t.access_token, refresh_token: t.refresh_token }));
  else localStorage.removeItem(KEY);
}
