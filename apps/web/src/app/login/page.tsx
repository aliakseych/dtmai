"use client";
import Link from "next/link";
import { useState, type FormEvent } from "react";
import { Button } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { AuthFrame, Field } from "@/components/auth/AuthFrame";
import { OrDivider } from "@/components/auth/OrDivider";
import { TelegramLogin } from "@/components/auth/TelegramLogin";
import { useSignedIn } from "@/components/auth/useSignedIn";
import { api } from "@/lib/api";
import { authErrorKey, isCode } from "@/lib/errors";

export default function LoginPage() {
  const t = useT();
  const signedIn = useSignedIn();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<ReturnType<typeof authErrorKey> | null>(null);
  const [unverified, setUnverified] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setUnverified(false);
    try {
      await signedIn(await api.unwrap(api.client.POST("/v1/identity/login", { body: { email, password } })));
    } catch (err) {
      setError(authErrorKey(err));
      setUnverified(isCode(err, "email_not_verified"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthFrame
      title={t("auth.login.title")}
      footer={
        <>
          {t("auth.noAccount")}{" "}
          <Link href="/register/" className="font-extrabold text-[#0d6fa0] underline">
            {t("auth.register.title")}
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Field label={t("auth.email")} type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <Field label={t("auth.password")} type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && (
          <p role="alert" className="font-bold text-red-deep">
            {t(error)}{" "}
            {unverified && (
              <Link href={`/register/?verify=${encodeURIComponent(email)}`} className="underline">
                {t("auth.verify")}
              </Link>
            )}
          </p>
        )}
        <Link href="/forgot/" className="self-start text-sm font-extrabold text-[#0d6fa0] underline">
          {t("auth.forgot.link")}
        </Link>
        <Button type="submit" block disabled={busy}>
          {t("auth.login.cta")}
        </Button>
      </form>
      <OrDivider />
      <TelegramLogin />
    </AuthFrame>
  );
}
