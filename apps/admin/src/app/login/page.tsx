"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { LocaleSwitcher } from "@dtmai/i18n";
import { Logo } from "@dtmai/ui";
import { useT } from "@/lib/i18n";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@dtmai/api-client";
import { errMsg } from "@/lib/util";
import { Btn, Field, Input } from "@/components/ui/controls";

export default function LoginPage() {
  const { login, me, loading } = useAuth();
  const router = useRouter();
  const t = useT();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (loading || !me) return;
    const next = new URLSearchParams(window.location.search).get("next");
    // Resolve before trusting: "/\\evil.com" or "/%09/evil.com" pass a prefix check but leave the origin.
    const u = next ? new URL(next, window.location.origin) : null;
    router.replace(u && u.origin === window.location.origin ? u.pathname + u.search + u.hash : "/");
  }, [loading, me, router]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await login(email, password);
    } catch (x) {
      setErr(x instanceof ApiError && x.status === 401 ? t("admin.login.badCredentials") : errMsg(x));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="grid min-h-screen place-items-center p-4">
      <form onSubmit={submit} className="w-full max-w-sm space-y-3 rounded-card border-2 border-line bg-white p-5">
        <div className="flex justify-center"><Logo size={44} /></div>
        <div className="flex items-center justify-between gap-2"><h1 className="text-lg text-brand">{t("admin.login.title")}</h1><LocaleSwitcher /></div>
        <Field label={t("admin.login.email")}><Input type="email" autoFocus required autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
        <Field label={t("admin.login.password")}><Input type="password" required autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} /></Field>
        {err && <p role="alert" className="text-sm font-bold text-red-deep">{err}</p>}
        <Btn variant="primary" type="submit" disabled={busy} className="w-full">{busy ? t("admin.login.signingIn") : t("admin.login.signIn")}</Btn>
      </form>
    </div>
  );
}
