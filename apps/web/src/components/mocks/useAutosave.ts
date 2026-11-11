"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { apiUrl } from "@/lib/env";
import { readTokens } from "@/lib/session";
import { withTmaReauth } from "@/lib/tma";
import type { Response } from "@/components/lesson/QuestionBody";

export type SaveState = "idle" | "saving" | "saved" | "error";
type Pending = { answers: Record<string, Response>; flags?: string[] };

const DEBOUNCE_MS = 800;
const isEmpty = (p: Pending) => Object.keys(p.answers).length === 0 && p.flags === undefined;

/**
 * Debounced autosave of an attempt. Changes are merged into one pending patch; a failed
 * request keeps the patch (merged under newer edits) so `flush()` is a real retry.
 * `onRejected` fires when the server refuses the save because the deadline passed.
 * On unmount and when the page is hidden/closed, unsaved edits are sent with `fetch(..., { keepalive: true })`.
 */
export function useAutosave(attemptId: string, onRejected: () => void) {
  const [state, setState] = useState<SaveState>("idle");
  const pending = useRef<Pending>({ answers: {} });
  /** Batch currently in flight; it may die with the page, so the keepalive send repeats it. */
  const sending = useRef<Pending | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const running = useRef<Promise<boolean> | null>(null);
  const deadlinePassed = useRef(false);
  const rejected = useRef(onRejected);
  rejected.current = onRejected;

  const flush = useCallback((): Promise<boolean> => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
    if (running.current) return running.current;
    const run = (async () => {
      try {
        while (!isEmpty(pending.current)) {
          const batch = pending.current;
          pending.current = { answers: {} };
          sending.current = batch;
          setState("saving");
          try {
            const r = await withTmaReauth(() =>
              api.unwrap(
                api.client.PATCH("/v1/assessment/attempts/{attempt_id}", {
                  params: { path: { attempt_id: attemptId } },
                  body: { answers: Object.keys(batch.answers).length ? batch.answers : undefined, flags: batch.flags },
                }),
              ),
            );
            if (!r.accepted) {
              deadlinePassed.current = true;
              setState("error");
              rejected.current();
              return false;
            }
          } catch {
            pending.current = { answers: { ...batch.answers, ...pending.current.answers }, flags: pending.current.flags ?? batch.flags };
            setState("error");
            return false;
          } finally {
            sending.current = null;
          }
        }
        setState("saved");
        return true;
      } finally {
        running.current = null;
      }
    })();
    running.current = run;
    return run;
  }, [attemptId]);

  const queue = useCallback(
    (patch: Pending) => {
      pending.current = { answers: { ...pending.current.answers, ...patch.answers }, flags: patch.flags ?? pending.current.flags };
      setState("saving");
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => void flush(), DEBOUNCE_MS);
    },
    [flush],
  );

  /** Fire-and-forget send that survives page teardown. Re-sending a patch is idempotent (answers are overwritten). */
  const flushKeepalive = useCallback(() => {
    const inflight = sending.current;
    const batch: Pending = {
      answers: { ...inflight?.answers, ...pending.current.answers },
      flags: pending.current.flags ?? inflight?.flags,
    };
    if (isEmpty(batch) || deadlinePassed.current) return;
    const token = readTokens()?.access_token;
    void fetch(`${apiUrl().replace(/\/+$/, "")}/v1/assessment/attempts/${attemptId}`, {
      method: "PATCH",
      keepalive: true,
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ answers: Object.keys(batch.answers).length ? batch.answers : undefined, flags: batch.flags }),
    }).catch(() => {});
  }, [attemptId]);

  useEffect(() => {
    const onHide = () => {
      if (document.visibilityState === "hidden") flushKeepalive();
    };
    window.addEventListener("pagehide", flushKeepalive);
    document.addEventListener("visibilitychange", onHide);
    return () => {
      window.removeEventListener("pagehide", flushKeepalive);
      document.removeEventListener("visibilitychange", onHide);
      if (timer.current) clearTimeout(timer.current);
      flushKeepalive();
    };
  }, [flushKeepalive]);

  const dirty = useCallback(() => !isEmpty(pending.current) || running.current !== null, []);
  const wasRejected = useCallback(() => deadlinePassed.current, []);
  return { state, queue, flush, dirty, wasRejected };
}
