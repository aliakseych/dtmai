"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { MockRunner } from "@/components/mocks/MockRunner";
import { RequireAuth } from "@/lib/auth";

/** ?attempt=<id> */
function Run() {
  const id = useSearchParams().get("attempt");
  const router = useRouter();
  useEffect(() => {
    if (!id) router.replace("/mocks/");
  }, [id, router]);
  return id ? <MockRunner attemptId={id} /> : null;
}

export default function MockRunPage() {
  return (
    <RequireAuth>
      <Suspense>
        <Run />
      </Suspense>
    </RequireAuth>
  );
}
