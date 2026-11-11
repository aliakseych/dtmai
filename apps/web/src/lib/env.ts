declare global {
  interface Window {
    __ENV__?: { API_URL?: string; MEDIA_URL?: string };
  }
}

/** API origin: runtime `window.__ENV__.API_URL`, else build-time NEXT_PUBLIC_API_URL. */
export function apiUrl(): string {
  const rt = typeof window !== "undefined" ? window.__ENV__?.API_URL : "";
  return rt || process.env.NEXT_PUBLIC_API_URL || "https://api.dtm-ai.uz";
}

/** Public base for media keys (`{type:"image", key}`). */
export function mediaUrl(key: string): string {
  if (/^https?:\/\//.test(key)) return key;
  const base = (typeof window !== "undefined" ? window.__ENV__?.MEDIA_URL : "") || process.env.NEXT_PUBLIC_MEDIA_URL || "";
  return `${base.replace(/\/+$/, "")}/${key.replace(/^\/+/, "")}`;
}
