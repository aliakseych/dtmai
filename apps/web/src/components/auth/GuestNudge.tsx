"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useT } from "@dtmai/i18n";
import { useStats } from "@/lib/stats";

const DONE_KEY = "dtmai.guest.firstLessonDone";
const DISMISS_KEY = "dtmai.guest.nudgeDismissed";
const read = (k: string) => {
  try {
    return localStorage.getItem(k) === "1";
  } catch {
    return false;
  }
};
const write = (k: string) => {
  try {
    localStorage.setItem(k, "1");
  } catch {
    /* storage unavailable: the nudge just reappears next visit */
  }
};

/** Soft, dismissible reminder for guests after their first completed lesson; never blocks. */
export function GuestNudge() {
  const t = useT();
  const { state } = useStats();
  const [done, setDone] = useState(false);
  const [dismissed, setDismissed] = useState(true);
  useEffect(() => {
    setDone(read(DONE_KEY));
    setDismissed(read(DISMISS_KEY));
  }, []);
  useEffect(() => {
    if (state.status === "ready" && state.data.lessons_completed > 0 && !read(DONE_KEY)) {
      write(DONE_KEY);
      setDone(true);
    }
  }, [state]);
  if (!done || dismissed) return null;
  const s = state.status === "ready" ? state.data : null;
  return (
    <div role="status" className="flex flex-col gap-1 bg-blue-soft px-4 py-3 text-sm">
      <div className="flex flex-wrap items-center justify-center gap-3 font-bold text-blue-deep">
        <span>{t("guest.nudge.text")}</span>
        <Link href="/register/" className="underline">
          {t("guest.nudge.cta")}
        </Link>
        <button
          type="button"
          className="text-ink-soft underline"
          onClick={() => {
            write(DISMISS_KEY);
            setDismissed(true);
          }}
        >
          {t("guest.nudge.dismiss")}
        </button>
      </div>
      {s && (s.xp_total > 0 || s.streak > 0) && (
        <p className="text-center text-ink-soft">{t("guest.nudge.warn", { xp: s.xp_total, streak: s.streak })}</p>
      )}
    </div>
  );
}
