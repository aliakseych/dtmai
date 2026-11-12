"use client";
import type { Tokens } from "@dtmai/api-client";
import { useLocale, useT } from "@dtmai/i18n";
import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { GuestNudge } from "@/components/auth/GuestNudge";
import { api, setApiLocale, setUnauthorizedHandler, type Language, type Me } from "./api";
import { contentLang } from "./localized";
import { readTokens, writeTokens } from "./session";
import { resetStats } from "./stats";

const MERGE_KEY = "dtmai.pendingGuestToken";
const readPending = () => {
  try {
    return sessionStorage.getItem(MERGE_KEY);
  } catch {
    return null;
  }
};
const writePending = (v: string | null) => {
  try {
    if (v) sessionStorage.setItem(MERGE_KEY, v);
    else sessionStorage.removeItem(MERGE_KEY);
  } catch {
    /* storage unavailable: the in-memory copy still serves this tab */
  }
};

type Ctx = {
  me: Me | null;
  loading: boolean;
  isGuest: boolean;
  /** Target lyceum + education language chosen (onboarding done). */
  onboarded: boolean;
  /** A guest's progress could not be merged into the account yet; the guest token is kept for `retryMerge`. */
  mergePending: boolean;
  retryMerge: () => Promise<void>;
  dismissMerge: () => void;
  startGuest: () => Promise<void>;
  /** Stores a freshly issued session; a current guest's progress is merged into it. */
  acceptTokens: (t: Tokens) => Promise<Me>;
  logout: () => Promise<void>;
  reloadMe: () => Promise<void>;
};
const AuthCtx = createContext<Ctx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const { locale } = useLocale();
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [pendingGuest, setPendingGuest] = useState<string | null>(null);
  setApiLocale(locale);

  const fetchMe = useCallback(async (): Promise<Me | null> => {
    if (!readTokens()) return null;
    try {
      return await api.unwrap(api.client.GET("/v1/identity/me"));
    } catch {
      return null;
    }
  }, []);

  const reloadMe = useCallback(async () => setMe(await fetchMe()), [fetchMe]);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      writeTokens(null);
      setMe(null);
      // Inside the Telegram Mini App, silently re-sign-in with the launch initData.
      void import("./tma").then(({ reauthTma }) => reauthTma()).then((ok) => { if (ok) void reloadMe(); });
    });
    setPendingGuest(readPending());
    void fetchMe().then((m) => {
      setMe(m);
      setLoading(false);
    });
  }, [fetchMe, reloadMe]);

  const startGuest = useCallback(async () => {
    if (readTokens() && (await fetchMe())) return reloadMe();
    writeTokens(await api.unwrap(api.client.POST("/v1/identity/guest")));
    resetStats();
    await reloadMe();
  }, [fetchMe, reloadMe]);

  const setPending = useCallback((v: string | null) => {
    writePending(v);
    setPendingGuest(v);
  }, []);

  const merge = useCallback(
    async (guestToken: string) => {
      try {
        await api.unwrap(api.client.POST("/v1/learning/merge-guest", { body: { guest_access_token: guestToken } }));
        setPending(null);
      } catch {
        // Keep the guest token so the merge can be retried; never drop the progress silently.
        setPending(guestToken);
      }
    },
    [setPending],
  );

  const acceptTokens = useCallback(
    async (t: Tokens) => {
      const guestToken = me?.roles.includes("guest") ? readTokens()?.access_token : undefined;
      writeTokens(t);
      resetStats();
      if (guestToken) await merge(guestToken);
      const next = await api.unwrap(api.client.GET("/v1/identity/me"));
      setMe(next);
      return next;
    },
    [me, merge],
  );

  const retryMerge = useCallback(async () => {
    if (pendingGuest) await merge(pendingGuest);
    resetStats();
  }, [pendingGuest, merge]);

  const logout = useCallback(async () => {
    const rt = readTokens()?.refresh_token;
    try {
      if (rt) await api.client.POST("/v1/identity/logout", { body: { refresh_token: rt } });
    } catch {
      /* the local session is dropped regardless */
    }
    writeTokens(null);
    resetStats();
    // Hard navigation: clearing `me` first would let RequireAuth mint a new guest before the landing page loads.
    window.location.assign("/");
  }, []);

  const value = useMemo<Ctx>(
    () => ({
      me,
      loading,
      isGuest: !!me?.roles.includes("guest"),
      onboarded: !!me?.dream_lyceum_ids.length && !!me?.education_language_id,
      mergePending: !!pendingGuest && !!me && !me.roles.includes("guest"),
      retryMerge,
      dismissMerge: () => setPending(null),
      startGuest,
      acceptTokens,
      logout,
      reloadMe,
    }),
    [me, loading, pendingGuest, retryMerge, setPending, startGuest, acceptTokens, logout, reloadMe],
  );
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export function useAuth(): Ctx {
  const c = useContext(AuthCtx);
  if (!c) throw new Error("AuthProvider missing");
  return c;
}

/** Where to go after a session is established. */
export const homeFor = (me: Me) => (me.dream_lyceum_ids.length > 0 && me.education_language_id ? "/home/" : "/onboarding/");

function MergeBanner() {
  const t = useT();
  const { mergePending, retryMerge, dismissMerge } = useAuth();
  const [busy, setBusy] = useState(false);
  if (!mergePending) return null;
  return (
    <div role="alert" className="flex flex-wrap items-center justify-center gap-3 bg-accent/20 px-4 py-2 text-sm font-bold">
      <span>{t("auth.merge.failed")}</span>
      <button
        type="button"
        disabled={busy}
        className="underline"
        onClick={() => {
          setBusy(true);
          void retryMerge().finally(() => setBusy(false));
        }}
      >
        {t("auth.merge.retry")}
      </button>
      <button type="button" className="text-ink-soft underline" onClick={dismissMerge}>
        {t("auth.merge.dismiss")}
      </button>
    </div>
  );
}

/**
 * Guest-first: an anonymous visitor on any page gets a guest session (falling back to /login/ only if that fails),
 * and a user without a target lyceum is sent to /onboarding/.
 */
/** `account`: guests are sent to `/account/` (like the (app) routes) instead of using the page. */
export function RequireAuth({ children, allowUnonboarded, account }: { children: ReactNode; allowUnonboarded?: boolean; account?: boolean }) {
  const { me, loading, onboarded, isGuest, startGuest } = useAuth();
  const router = useRouter();
  const starting = useRef(false);
  useEffect(() => {
    if (loading) return;
    if (!me) {
      if (starting.current) return;
      starting.current = true;
      startGuest()
        .catch(() => router.replace("/login/"))
        .finally(() => {
          starting.current = false;
        });
    } else if (!onboarded && !allowUnonboarded) router.replace("/onboarding/");
    else if (account && isGuest) router.replace("/account/");
  }, [loading, me, onboarded, allowUnonboarded, account, isGuest, router, startGuest]);
  if (loading || !me || (!onboarded && !allowUnonboarded) || (account && isGuest)) return <div className="grid min-h-dvh place-items-center" aria-busy="true" />;
  return (
    <>
      <MergeBanner />
      {isGuest && onboarded && <GuestNudge />}
      {children}
    </>
  );
}

let languages: Promise<Language[]> | null = null;
/** edu.uz education-language classifier code → content language ("12" Russian, "14" English, anything else Uzbek/Karakalpak). */
export const contentLangOfCode = (code: string): "uz" | "ru" | "en" => (code === "12" ? "ru" : code === "14" ? "en" : "uz");

/** Content language of the learner's education language, independent of the UI locale (UI locale only until it is known). */
export function useLearnLanguage(): "uz" | "ru" | "en" {
  const { me } = useAuth();
  const { locale } = useLocale();
  const [code, setCode] = useState<string | null>(null);
  const id = me?.education_language_id;
  useEffect(() => {
    if (!id) return;
    languages ??= api.unwrap(api.client.GET("/v1/lyceums/languages"));
    languages.then((ls) => setCode(ls.find((l) => l.id === id)?.code ?? null)).catch(() => (languages = null));
  }, [id]);
  return code ? contentLangOfCode(code) : contentLang(locale);
}
