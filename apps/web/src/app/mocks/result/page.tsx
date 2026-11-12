"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { MockResult } from "@/components/mocks/MockResult";
import { RequireAuth } from "@/lib/auth";

/** ?attempt=<id> */
function Result() {
  const id = useSearchParams().get("attempt");
  const router = useRouter();
  useEffect(() => {
    if (!id) router.replace("/mocks/");
  }, [id, router]);
  return id ? <MockResult attemptId={id} /> : null;
}

export default function MockResultPage() {
  return (
    <RequireAuth>
      <Suspense>
        <Result />
      </Suspense>
    </RequireAuth>
  );
}
