"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "@/lib/auth";
import { errMsg } from "@/lib/util";
import { Btn, Field, Input } from "@/components/ui/controls";

export default function LoginPage() {
  const { login, me, loading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (!loading && me) router.replace("/questions/");
  }, [loading, me, router]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await login(email, password);
    } catch (x) {
      setErr(errMsg(x));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="grid h-screen place-items-center">
      <form onSubmit={submit} className="w-80 space-y-3 rounded-lg border border-line bg-white p-5 shadow">
        <h1 className="text-lg text-brand">DTM AI admin</h1>
        <Field label="Email"><Input type="email" autoFocus required autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
        <Field label="Password"><Input type="password" required autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} /></Field>
        {err && <p className="text-xs font-bold text-red-deep">{err}</p>}
        <Btn variant="primary" type="submit" disabled={busy} className="w-full">{busy ? "Signing in…" : "Sign in"}</Btn>
      </form>
    </div>
  );
}
