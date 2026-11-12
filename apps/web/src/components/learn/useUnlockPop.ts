"use client";
import { useEffect, useRef } from "react";

const KEY = "dtmai.path.open";

/** Returns the ids of lessons that became open since this device last rendered the path (they get a pop-in). First visit pops nothing. */
export function useUnlockPop(openIds: string[]): Set<string> {
  const fresh = useRef<Set<string>>(new Set());
  const joined = openIds.join(",");
  if (typeof window !== "undefined" && fresh.current.size === 0 && openIds.length > 0) {
    try {
      const raw = window.localStorage.getItem(KEY);
      if (raw !== null) {
        const known = new Set(raw.split(",").filter(Boolean));
        fresh.current = new Set(openIds.filter((id) => !known.has(id)));
      }
    } catch {
      /* storage unavailable: no pop */
    }
  }
  useEffect(() => {
    try {
      const known = new Set((window.localStorage.getItem(KEY) ?? "").split(",").filter(Boolean));
      for (const id of joined.split(",").filter(Boolean)) known.add(id);
      window.localStorage.setItem(KEY, [...known].join(","));
    } catch {
      /* storage unavailable */
    }
  }, [joined]);
  return fresh.current;
}
