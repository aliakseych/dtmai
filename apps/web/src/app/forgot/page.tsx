"use client";
import Link from "next/link";
import { useState, type FormEvent } from "react";
import { Button } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { AuthFrame, Field } from "@/components/auth/AuthFrame";
import { useSignedIn } from "@/components/auth/useSignedIn";
import { api } from "@/lib/api";
import { authErrorKey } from "@/lib/errors";

export default function ForgotPage() {
  const t = useT();
  const signedIn = useSignedIn();
  const [step, setStep] = useState<"email" | "reset">("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<ReturnType<typeof authErrorKey> | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (step === "email") {
        await api.unwrap(api.client.POST("/v1/identity/password/forgot", { body: { email } }));
        setStep("reset");
      } else {
        await signedIn(await api.unwrap(api.client.POST("/v1/identity/password/reset", { body: { email, code, password } })));
      }
    } catch (err) {
      setError(authErrorKey(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthFrame
      title={t("auth.forgot.title")}
      footer={
        <Link href="/login/" className="font-extrabold text-[#0d6fa0] underline">
          {t("auth.login.title")}
        </Link>
      }
    >
      <form onSubmit={submit} className="flex flex-col gap-4">
        {step === "email" ? (
          <Field label={t("auth.email")} type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        ) : (
          <>
            <p className="text-ink-soft">{t("auth.codeSent", { email })}</p>
            <Field label={t("auth.code")} inputMode="numeric" autoComplete="one-time-code" required value={code} onChange={(e) => setCode(e.target.value)} />
            <Field label={t("auth.forgot.newPassword")} type="password" autoComplete="new-password" minLength={8} required value={password} onChange={(e) => setPassword(e.target.value)} />
          </>
        )}
        {error && (
          <p role="alert" className="font-bold text-red-deep">
            {t(error)}
          </p>
        )}
        <Button type="submit" block disabled={busy}>
          {step === "email" ? t("auth.forgot.send") : t("auth.forgot.reset")}
        </Button>
      </form>
    </AuthFrame>
  );
}
