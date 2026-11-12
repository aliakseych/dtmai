"use client";
import Link from "next/link";
import { Suspense, useState, type FormEvent } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { AuthFrame, Field } from "@/components/auth/AuthFrame";
import { useSignedIn } from "@/components/auth/useSignedIn";
import { api } from "@/lib/api";
import { useRedirectIfSignedIn } from "@/components/auth/useRedirectIfSignedIn";
import { authErrorKey, checkEmail, checkPassword, checkRequired, serverFieldErrors, type FieldErrors } from "@/lib/errors";

function ForgotForm() {
  const t = useT();
  const signedIn = useSignedIn();
  useRedirectIfSignedIn();
  const [fields, setFields] = useState<FieldErrors>({});
  const [info, setInfo] = useState(false);
  const [step, setStep] = useState<"email" | "reset">("email");
  const [email, setEmail] = useState(useSearchParams().get("email") ?? "");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<ReturnType<typeof authErrorKey> | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const found: FieldErrors = {};
    if (step === "email") {
      const em = checkEmail(email);
      if (em) found.email = em;
    } else {
      const c = checkRequired(code);
      const pw = checkPassword(password);
      if (c) found.code = c;
      if (pw) found.password = pw;
    }
    setFields(found);
    if (Object.keys(found).length) return;
    setBusy(true);
    setError(null);
    setInfo(false);
    try {
      if (step === "email") {
        await api.unwrap(api.client.POST("/v1/identity/password/forgot", { body: { email } }));
        setStep("reset");
      } else {
        await signedIn(await api.unwrap(api.client.POST("/v1/identity/password/reset", { body: { email, code, password } })));
      }
    } catch (err) {
      const fe = serverFieldErrors(err);
      setFields(fe);
      if (!Object.keys(fe).length) setError(authErrorKey(err));
    } finally {
      setBusy(false);
    }
  }

  async function resend() {
    setError(null);
    try {
      await api.unwrap(api.client.POST("/v1/identity/password/forgot", { body: { email } }));
      setInfo(true);
    } catch (err) {
      setError(authErrorKey(err));
    }
  }

  return (
    <AuthFrame
      title={t("auth.forgot.title")}
      footer={
        <Link href="/login/" className="font-extrabold text-brand underline">
          {t("auth.login.title")}
        </Link>
      }
    >
      <form onSubmit={submit} noValidate className="flex flex-col gap-4">
        {step === "email" ? (
          <Field label={t("auth.email")} type="email" autoComplete="email" error={fields.email && t(fields.email)} value={email} onChange={(e) => setEmail(e.target.value)} />
        ) : (
          <>
            <p className="text-ink-soft">{t("auth.codeSent", { email })}</p>
            <Field label={t("auth.code")} inputMode="numeric" autoComplete="one-time-code" error={fields.code && t(fields.code)} value={code} onChange={(e) => setCode(e.target.value)} />
            <Field label={t("auth.forgot.newPassword")} type="password" autoComplete="new-password" reveal hint={t("auth.password.hint")} error={fields.password && t(fields.password)} value={password} onChange={(e) => setPassword(e.target.value)} />
            <div className="flex flex-wrap gap-4 text-sm font-extrabold text-brand underline">
              <button type="button" onClick={resend}>
                {t("auth.resend")}
              </button>
              <button type="button" onClick={() => { setStep("email"); setCode(""); setFields({}); setError(null); setInfo(false); }}>
                {t("auth.changeEmail")}
              </button>
            </div>
            {info && <p role="status" className="text-sm font-bold text-correct-deep">{t("auth.resent")}</p>}
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

export default function ForgotPage() {
  return (
    <Suspense>
      <ForgotForm />
    </Suspense>
  );
}
