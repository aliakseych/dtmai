"use client";
import { ApiError, NetworkError } from "@dtmai/api-client";
import { useLocale } from "@dtmai/i18n";
import { useCallback, useEffect, useRef, useState } from "react";

export type ErrorKind = "offline" | "auth" | "server";
export type AsyncState<T> =
  | { status: "loading" }
  | { status: "error"; error: Error; kind: ErrorKind }
  | { status: "ready"; data: T; refreshing: boolean };

export function errorKind(e: unknown): ErrorKind {
  if (e instanceof NetworkError) return "offline";
  if (e instanceof ApiError && e.status === 401) return "auth";
  return "server";
}

/**
 * Loads data on mount, on dep change and on locale change (content is localized server-side).
 * Reloads keep the previous data on screen instead of flashing the skeleton.
 */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const { locale } = useLocale();
  const [state, setState] = useState<AsyncState<T>>({ status: "loading" });
  const [tick, setTick] = useState(0);
  const fnRef = useRef(fn);
  fnRef.current = fn;
  const key = JSON.stringify(deps);
  const lastKey = useRef(key);

  useEffect(() => {
    let live = true;
    const depsChanged = lastKey.current !== key;
    lastKey.current = key;
    setState((s) => (s.status === "ready" && !depsChanged ? { ...s, refreshing: true } : { status: "loading" }));
    fnRef.current().then(
      (data) => live && setState({ status: "ready", data, refreshing: false }),
      (error: Error) => live && setState({ status: "error", error, kind: errorKind(error) }),
    );
    return () => {
      live = false;
    };
  }, [key, locale, tick]);

  const reload = useCallback(() => setTick((n) => n + 1), []);
  return { state, reload };
}
