"use client";
import { useEffect, useState } from "react";

/** Seconds remaining until an ISO instant (0 when past or unset); ticks every second. */
export function useCountdown(iso: string | null | undefined): number {
  const target = iso ? Date.parse(iso) : NaN;
  const calc = () => (Number.isNaN(target) ? 0 : Math.max(0, Math.ceil((target - Date.now()) / 1000)));
  const [left, setLeft] = useState(calc);
  useEffect(() => {
    setLeft(calc());
    if (Number.isNaN(target)) return;
    const id = setInterval(() => setLeft(calc()), 1000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target]);
  return left;
}

export const clock = (s: number) => {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const p = (n: number) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${p(m)}:${p(s % 60)}` : `${p(m)}:${p(s % 60)}`;
};
