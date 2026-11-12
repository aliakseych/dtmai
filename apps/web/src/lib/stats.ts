"use client";
import { useCallback, useEffect, useSyncExternalStore } from "react";
import { api, type Stats } from "./api";
import { errorKind, type AsyncState } from "./useAsync";

/** One shared, cached stats query (`GET /v1/me/stats`); every consumer sees the same data and `refreshStats` updates all of them. */
let snapshot: AsyncState<Stats> = { status: "loading" };
let inflight: Promise<Stats> | null = null;
const listeners = new Set<() => void>();
const LOADING: AsyncState<Stats> = { status: "loading" };

const publish = (s: AsyncState<Stats>) => {
  snapshot = s;
  listeners.forEach((l) => l());
};

/** Refetches stats and updates every subscriber; concurrent calls share one request. */
export function refreshStats(): Promise<Stats> {
  if (inflight) return inflight;
  if (snapshot.status === "ready") publish({ ...snapshot, refreshing: true });
  const p = api
    .unwrap(api.client.GET("/v1/me/stats"))
    .then((data) => {
      publish({ status: "ready", data, refreshing: false });
      return data;
    })
    .catch((error: Error) => {
      publish({ status: "error", error, kind: errorKind(error) });
      throw error;
    })
    .finally(() => {
      inflight = null;
    });
  inflight = p;
  return p;
}

/** Drops cached stats when the session changes (login, logout, guest start). */
export function resetStats() {
  inflight = null;
  publish(LOADING);
}

const subscribe = (l: () => void) => {
  listeners.add(l);
  return () => void listeners.delete(l);
};

/** Current learner stats; cached and shared, revalidated on mount. */
export function useStats() {
  const state = useSyncExternalStore(subscribe, () => snapshot, () => LOADING);
  useEffect(() => {
    void refreshStats().catch(() => undefined);
  }, []);
  const reload = useCallback(() => void refreshStats().catch(() => undefined), []);
  return { state, reload };
}

/** A subject with cards due for review, or null when nothing is due anywhere. */
export async function pickReviewSubject(): Promise<string | null> {
  const subjects = await api.unwrap(api.client.GET("/v1/catalog/subjects"));
  const due = await Promise.all(
    subjects.map((s) =>
      api.unwrap(api.client.GET("/v1/learning/review/summary", { params: { query: { subject_id: s.id } } })).then(
        (r) => r.due,
        () => 0,
      ),
    ),
  );
  const i = due.findIndex((n) => n > 0);
  return i >= 0 ? subjects[i]!.id : null;
}
