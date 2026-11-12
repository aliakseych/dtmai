"use client";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { homeFor, useAuth } from "@/lib/auth";

/** Sends an already signed-in, non-guest user away from /login, /register and /forgot. */
export function useRedirectIfSignedIn(dest?: string) {
  const { me, loading, isGuest } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading && me && !isGuest) router.replace(dest ?? homeFor(me));
  }, [loading, me, isGuest, router, dest]);
}
