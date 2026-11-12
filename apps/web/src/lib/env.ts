declare global {
  interface Window {
    __ENV__?: { API_URL?: string; MEDIA_URL?: string };
  }
}

/** API origin: runtime `window.__ENV__.API_URL`, else build-time NEXT_PUBLIC_API_URL; dev never falls back to production. */
export function apiUrl(): string {
  const rt = typeof window !== "undefined" ? window.__ENV__?.API_URL : "";
  const fallback = process.env.NODE_ENV === "development" ? "http://localhost:8000" : "https://api.dtm-ai.uz";
  return rt || process.env.NEXT_PUBLIC_API_URL || fallback;
}

/** Public base for media keys (`{type:"image", key}`). */
export function mediaUrl(key: string): string {
  if (/^https?:\/\//.test(key)) return key;
  const base = (typeof window !== "undefined" ? window.__ENV__?.MEDIA_URL : "") || process.env.NEXT_PUBLIC_MEDIA_URL || "";
  return `${base.replace(/\/+$/, "")}/${key.replace(/^\/+/, "")}`;
}
