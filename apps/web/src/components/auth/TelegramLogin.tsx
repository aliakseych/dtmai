"use client";
import { useEffect, useRef, useState } from "react";
import { useT } from "@dtmai/i18n";
import { api } from "@/lib/api";
import { authErrorKey } from "@/lib/errors";
import { useSignedIn } from "./useSignedIn";

type TgUser = { id: number | string; auth_date: number | string; hash: string; first_name?: string; last_name?: string; photo_url?: string; username?: string };

declare global {
  interface Window {
    onDtmTelegramAuth?: (user: TgUser) => void;
  }
}

/** Official Telegram Login Widget; bot username comes from NEXT_PUBLIC_TG_BOT. */
export function TelegramLogin() {
  const t = useT();
  const host = useRef<HTMLDivElement>(null);
  const signedIn = useSignedIn();
  const signedInRef = useRef(signedIn);
  signedInRef.current = signedIn;
  const [error, setError] = useState<ReturnType<typeof authErrorKey> | null>(null);
  const bot = process.env.NEXT_PUBLIC_TG_BOT;

  useEffect(() => {
    if (!bot || !host.current) return;
    window.onDtmTelegramAuth = async (u) => {
      try {
        await signedInRef.current(
          await api.unwrap(
            api.client.POST("/v1/identity/telegram/widget", {
              body: { ...u, id: Number(u.id), auth_date: Number(u.auth_date) } as never,
            }),
          ),
        );
      } catch (e) {
        setError(authErrorKey(e));
      }
    };
    const s = document.createElement("script");
    s.src = "https://telegram.org/js/telegram-widget.js?22";
    s.async = true;
    s.dataset.telegramLogin = bot;
    s.dataset.size = "large";
    s.dataset.radius = "16";
    s.dataset.onauth = "onDtmTelegramAuth(user)";
    s.dataset.requestAccess = "write";
    const el = host.current;
    el.appendChild(s);
    return () => {
      el.replaceChildren();
      delete window.onDtmTelegramAuth;
    };
  }, [bot]);

  return (
    <>
      <div ref={host} className="flex min-h-[40px] justify-center" />
      {error && (
        <p role="alert" className="text-center font-bold text-red-deep">
          {t(error)}
        </p>
      )}
    </>
  );
}
