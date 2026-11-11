"use client";
import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Button } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

/** "This is my dream lyceum": PATCH /me target_lyceum_id, then a floating-hearts burst. */
export function DreamButton({ lyceumId, onChanged }: { lyceumId: string; onChanged?: () => void }) {
  const t = useT();
  const { me, reloadMe } = useAuth();
  const reduce = useReducedMotion();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const [burst, setBurst] = useState(0);
  const mine = me?.target_lyceum_id === lyceumId;

  const choose = async () => {
    setBusy(true);
    setError(false);
    try {
      await api.unwrap(api.client.PATCH("/v1/identity/me", { body: { target_lyceum_id: lyceumId } }));
      await reloadMe();
      setBurst((n) => n + 1);
      onChanged?.();
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="relative inline-flex flex-col items-start gap-2">
      <Button variant={mine ? "secondary" : "super"} disabled={busy || mine} onClick={choose} aria-live="polite">
        <motion.img
          src="/brand/icon-heart.png"
          alt=""
          width={22}
          height={22}
          key={`${mine}`}
          initial={reduce ? false : { scale: 0.4 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 500, damping: 12 }}
        />
        {mine ? t("lyceums.dream.mine") : t("lyceums.dream.cta")}
      </Button>
      {error && <p role="alert" className="text-sm font-bold text-red">{t("common.error")}</p>}
      <AnimatePresence>
        {!reduce &&
          burst > 0 &&
          [0, 1, 2, 3, 4].map((i) => (
            <motion.img
              key={`${burst}-${i}`}
              src="/brand/icon-heart.png"
              alt=""
              aria-hidden="true"
              width={20}
              height={20}
              className="pointer-events-none absolute left-6 top-0"
              initial={{ opacity: 1, y: 0, x: 0, scale: 0.6 }}
              animate={{ opacity: 0, y: -70 - i * 8, x: (i - 2) * 22, scale: 1.2 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.9, delay: i * 0.05, ease: "easeOut" }}
            />
          ))}
      </AnimatePresence>
    </div>
  );
}
