"use client";
import { useLocale } from "@dtmai/i18n";
import { api, type LyceumRow } from "@/lib/api";
import { pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";

/** Public lyceum list, fetched once; names resolve without auth (the detail endpoint needs a login). */
let list: Promise<LyceumRow[]> | undefined;
const loadList = () => {
  list ??= api.unwrap(api.client.GET("/v1/lyceums", { params: { query: { limit: 200 } } }));
  list.catch(() => (list = undefined));
  return list;
};

/** Localized lyceum name from the public list. */
export function LyceumName({ id }: { id: string }) {
  const { locale } = useLocale();
  const { state } = useAsync(loadList, []);
  const row = state.status === "ready" ? state.data.find((l) => l.id === id) : undefined;
  return <>{row ? pick(row.names, locale) : "…"}</>;
}
