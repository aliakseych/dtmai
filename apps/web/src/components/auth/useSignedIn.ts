"use client";
import type { Tokens } from "@dtmai/api-client";
import { useRouter } from "next/navigation";
import { homeFor, useAuth } from "@/lib/auth";

/** Accepts tokens (merging a guest) and routes to `dest`, or onboarding / the path. */
export function useSignedIn(dest?: string) {
  const { acceptTokens } = useAuth();
  const router = useRouter();
  return async (t: Tokens) => {
    const me = await acceptTokens(t);
    router.replace(dest ?? homeFor(me));
  };
}
