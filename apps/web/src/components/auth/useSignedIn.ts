"use client";
import type { Tokens } from "@dtmai/api-client";
import { useRouter } from "next/navigation";
import { homeFor, useAuth } from "@/lib/auth";

/** Accepts tokens (merging a guest) and routes to onboarding or the path. */
export function useSignedIn() {
  const { acceptTokens } = useAuth();
  const router = useRouter();
  return async (t: Tokens) => router.replace(homeFor(await acceptTokens(t)));
}
