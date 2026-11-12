"use client";
import { useEffect, useRef, useState } from "react";
import { useT } from "@dtmai/i18n";
import { api } from "@/lib/api";
import { authErrorKey } from "@/lib/errors";
import { useAsync } from "@/lib/useAsync";
import { useSignedIn } from "./useSignedIn";

type Credential = { credential: string };
type Gis = {
  accounts: {
    id: {
      initialize: (o: { client_id: string; callback: (r: Credential) => void }) => void;
      renderButton: (el: HTMLElement, o: Record<string, unknown>) => void;
    };
  };
};

const SRC = "https://accounts.google.com/gsi/client";
const gis = () => (window as unknown as { google?: Gis }).google;

function loadGis(): Promise<void> {
  if (gis()) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${SRC}"]`);
    const s = existing ?? Object.assign(document.createElement("script"), { src: SRC, async: true });
    s.addEventListener("load", () => resolve());
    s.addEventListener("error", () => reject(new Error("gis")));
    if (!existing) document.head.appendChild(s);
  });
}

/** "Sign in with Google" (Google Identity Services). Renders nothing unless the API reports a client id. */
export function GoogleSignIn({ dest }: { dest?: string }) {
  const t = useT();
  const cfg = useAsync(() => api.unwrap(api.client.GET("/v1/identity/config")), []);
  const clientId = cfg.state.status === "ready" ? cfg.state.data.google_client_id : null;
  const host = useRef<HTMLDivElement>(null);
  const signedIn = useSignedIn(dest);
  const signedInRef = useRef(signedIn);
  signedInRef.current = signedIn;
  const [error, setError] = useState<ReturnType<typeof authErrorKey> | null>(null);

  useEffect(() => {
    if (!clientId || !host.current) return;
    let alive = true;
    const el = host.current;
    loadGis()
      .then(() => {
        if (!alive) return;
        gis()!.accounts.id.initialize({
          client_id: clientId,
          callback: async ({ credential }) => {
            try {
              await signedInRef.current(await api.unwrap(api.client.POST("/v1/identity/google", { body: { id_token: credential } })));
            } catch (e) {
              setError(authErrorKey(e));
            }
          },
        });
        gis()!.accounts.id.renderButton(el, { type: "standard", theme: "outline", size: "large", shape: "pill", text: "continue_with", width: 320 });
      })
      .catch(() => alive && setError(authErrorKey(new Error("network"))));
    return () => {
      alive = false;
      el.replaceChildren();
    };
  }, [clientId]);

  if (!clientId) return null;
  return (
    <>
      <div ref={host} className="flex min-h-[44px] justify-center" aria-label={t("auth.google")} />
      {error && (
        <p role="alert" className="text-center font-bold text-red-deep">
          {t(error)}
        </p>
      )}
    </>
  );
}
