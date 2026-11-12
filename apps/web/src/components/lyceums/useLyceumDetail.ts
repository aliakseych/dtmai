"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { components } from "@dtmai/api-client";

export type LyceumDetailData = components["schemas"]["LyceumDetail"];

/** Detail cache shared by list cards, the open detail view and the learn-home pin. */
const cache = new Map<string, Promise<LyceumDetailData>>();

function load(id: string): Promise<LyceumDetailData> {
  let p = cache.get(id);
  if (!p) {
    p = api.unwrap(api.client.GET("/v1/lyceums/{lyceum_id}", { params: { path: { lyceum_id: id } } }));
    cache.set(id, p);
    p.catch(() => cache.delete(id));
  }
  return p;
}

/** `undefined` while loading, `null` on failure. `reload` refetches (e.g. after a dream change). */
export function useLyceumDetail(id: string | null | undefined) {
  const [data, setData] = useState<LyceumDetailData | null | undefined>(undefined);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (!id) {
      setData(null);
      return;
    }
    let live = true;
    load(id).then(
      (d) => live && setData(d),
      () => live && setData(null),
    );
    return () => {
      live = false;
    };
  }, [id, tick]);
  const reload = useCallback(() => {
    if (id) cache.delete(id);
    setTick((n) => n + 1);
  }, [id]);
  return { data, reload };
}

/** Latest-year competition ratio (applications per seat) across specialities, if any. */
export function latestCompetition(d: LyceumDetailData): number | null {
  const years = d.stats.map((s) => s.year);
  if (!years.length) return null;
  const y = Math.max(...years);
  const rows = d.stats.filter((s) => s.year === y);
  const quota = rows.reduce((a, r) => a + r.quota, 0);
  const apps = rows.reduce((a, r) => a + r.applications, 0);
  return quota > 0 ? apps / quota : null;
}
