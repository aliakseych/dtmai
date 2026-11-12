"use client";
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import type { components } from "@dtmai/api-client";
import { api, setUnauthorizedHandler } from "./api";
import { useT } from "./i18n";
import { readTokens, writeTokens } from "./session";

export type Me = components["schemas"]["MeOut"];
type State = { me: Me | null; loading: boolean };
type Ctx = State & {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAdmin: boolean;
  canEdit: boolean;
};
const AuthCtx = createContext<Ctx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [st, setSt] = useState<State>({ me: null, loading: true });

  const loadMe = useCallback(async () => {
    if (!readTokens()) return setSt({ me: null, loading: false });
    try {
      setSt({ me: await api.unwrap(api.client.GET("/v1/identity/me")), loading: false });
    } catch {
      setSt({ me: null, loading: false });
    }
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      writeTokens(null);
      setSt({ me: null, loading: false });
    });
    void loadMe();
  }, [loadMe]);

  const login = useCallback(
    async (email: string, password: string) => {
      const t = await api.unwrap(api.client.POST("/v1/identity/login", { body: { email, password } }));
      writeTokens(t);
      await loadMe();
    },
    [loadMe],
  );
  const logout = useCallback(async () => {
    const rt = readTokens()?.refresh_token;
    try {
      if (rt) await api.client.POST("/v1/identity/logout", { body: { refresh_token: rt } });
    } finally {
      writeTokens(null);
      setSt({ me: null, loading: false });
    }
  }, []);

  const value = useMemo<Ctx>(
    () => ({
      ...st,
      login,
      logout,
      isAdmin: !!st.me?.roles.includes("admin"),
      canEdit: !!st.me?.roles.some((r) => r === "admin" || r === "editor"),
    }),
    [st, login, logout],
  );
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export function useAuth(): Ctx {
  const c = useContext(AuthCtx);
  if (!c) throw new Error("AuthProvider missing");
  return c;
}

/** Client-side guard. The API enforces roles; this only avoids rendering the tool for non-staff. */
export function RequireAdmin({ children }: { children: ReactNode }) {
  const { me, loading, canEdit, logout } = useAuth();
  const router = useRouter();
  const t = useT();
  useEffect(() => {
    if (!loading && !me) {
      const here = window.location.pathname + window.location.search;
      router.replace(here === "/" || here.startsWith("/login") ? "/login/" : `/login/?next=${encodeURIComponent(here)}`);
    }
  }, [loading, me, router]);
  if (loading || !me) return <div className="grid h-screen place-items-center text-ink-soft">{t("admin.common.loading")}</div>;
  if (!canEdit)
    return (
      <div className="grid h-screen place-items-center">
        <div className="text-center">
          <h1 className="text-xl">{t("admin.auth.noAccess")}</h1>
          <p className="mt-1 text-ink-soft">{t("admin.auth.noRole", { email: me.email ?? "" })}</p>
          <button className="mt-3 rounded-xl border border-line bg-white px-3 py-1.5" onClick={() => void logout()}>
            {t("admin.common.signOut")}
          </button>
        </div>
      </div>
    );
  return <>{children}</>;
}
