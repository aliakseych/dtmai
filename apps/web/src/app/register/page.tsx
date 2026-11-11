"use client";
import Link from "next/link";
import { Suspense, useEffect, useState, type FormEvent } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AuthFrame, Field } from "@/components/auth/AuthFrame";
import { OrDivider } from "@/components/auth/OrDivider";
import { TelegramLogin } from "@/components/auth/TelegramLogin";
import { useSignedIn } from "@/components/auth/useSignedIn";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { authErrorKey } from "@/lib/errors";

function RegisterForm() {
  const t = useT();
  const { locale } = useLocale();
  const { isGuest } = useAuth();
  const signedIn = useSignedIn();
  const verify = useSearchParams().get("verify");
  const [step, setStep] = useState<"details" | "code">(verify ? "code" : "details");
  const [email, setEmail] = useState(verify ?? "");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<ReturnType<typeof authErrorKey> | null>(null);
  const [info, setInfo] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (verify) void api.client.POST("/v1/identity/email/resend", { body: { email: verify } });
  }, [verify]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setInfo(false);
    try {
      if (step === "details") {
        await api.unwrap(api.client.POST("/v1/identity/register", { body: { email, password, name, locale } }));
        setStep("code");
      } else {
        await signedIn(await api.unwrap(api.client.POST("/v1/identity/email/verify", { body: { email, code } })));
      }
    } catch (err) {
      setError(authErrorKey(err));
    } finally {
      setBusy(false);
    }
  }

  async function resend() {
    setError(null);
    try {
      await api.unwrap(api.client.POST("/v1/identity/email/resend", { body: { email } }));
      setInfo(true);
    } catch (err) {
      setError(authErrorKey(err));
    }
  }

  return (
    <AuthFrame
      title={isGuest ? t("auth.save.title") : t("auth.register.title")}
      footer={
        <>
          {t("auth.haveAccount")}{" "}
          <Link href="/login/" className="font-extrabold text-[#0d6fa0] underline">
            {t("auth.login.title")}
          </Link>
        </>
      }
    >
      {isGuest && <p className="text-center text-ink-soft">{t("auth.save.text")}</p>}
      <form onSubmit={submit} className="flex flex-col gap-4">
        {step === "details" ? (
          <>
            <Field label={t("auth.name")} autoComplete="name" required value={name} onChange={(e) => setName(e.target.value)} />
            <Field label={t("auth.email")} type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            <Field label={t("auth.password")} type="password" autoComplete="new-password" minLength={8} required value={password} onChange={(e) => setPassword(e.target.value)} />
          </>
        ) : (
          <>
            <p className="text-ink-soft">{t("auth.codeSent", { email })}</p>
            <Field label={t("auth.code")} inputMode="numeric" autoComplete="one-time-code" required value={code} onChange={(e) => setCode(e.target.value)} />
            <button type="button" onClick={resend} className="self-start text-sm font-extrabold text-[#0d6fa0] underline">
              {t("auth.resend")}
            </button>
            {info && <p role="status" className="text-sm font-bold text-[#2f6200]">{t("auth.resent")}</p>}
          </>
        )}
        {error && (
          <p role="alert" className="font-bold text-red-deep">
            {t(error)}
          </p>
        )}
        <Button type="submit" block disabled={busy}>
          {step === "details" ? t("auth.register.cta") : t("auth.verify")}
        </Button>
      </form>
      {step === "details" && (
        <>
          <OrDivider />
          <TelegramLogin />
        </>
      )}
    </AuthFrame>
  );
}

export default function RegisterPage() {
  return (
    <Suspense>
      <RegisterForm />
    </Suspense>
  );
}
