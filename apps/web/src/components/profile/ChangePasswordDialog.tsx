"use client";
import { useState, type FormEvent } from "react";
import { Button, Modal, buttonClass, useToast } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { Field } from "@/components/auth/AuthFrame";
import { api } from "@/lib/api";
import { authErrorKey, checkPassword, checkRequired } from "@/lib/errors";
import { ApiError } from "@dtmai/api-client";

/** Signed-in password change: current + new password. Other sessions stay valid. */
export function ChangePasswordDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const t = useT();
  const toast = useToast();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [errs, setErrs] = useState<{ current?: string; next?: string }>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function close() {
    setCurrent("");
    setNext("");
    setErrs({});
    setError(null);
    onClose();
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    const c = checkRequired(current);
    const n = checkPassword(next);
    setErrs({ current: c ? t(c) : undefined, next: n ? t(n) : undefined });
    setError(null);
    if (c || n) return;
    setBusy(true);
    try {
      await api.unwrap(api.client.POST("/v1/identity/password/change", { body: { current_password: current, new_password: next } }));
      toast(t("profile.password.done"), "success");
      close();
    } catch (err) {
      if (err instanceof ApiError && err.code === "wrong_password") setErrs({ current: t("profile.password.wrong") });
      else setError(t(authErrorKey(err)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal open={open} onClose={close} title={t("profile.changePassword")}>
      <form onSubmit={submit} noValidate className="flex flex-col gap-4">
        <Field label={t("profile.password.current")} type="password" autoComplete="current-password" reveal error={errs.current} value={current} onChange={(e) => setCurrent(e.target.value)} />
        <Field label={t("auth.forgot.newPassword")} type="password" autoComplete="new-password" reveal hint={t("auth.password.hint")} error={errs.next} value={next} onChange={(e) => setNext(e.target.value)} />
        {error && (
          <p role="alert" className="font-bold text-red-deep">
            {error}
          </p>
        )}
        <Button type="submit" block disabled={busy}>
          {t("profile.password.save")}
        </Button>
        <button type="button" onClick={close} className={buttonClass("secondary", true)}>
          {t("common.close")}
        </button>
      </form>
    </Modal>
  );
}
