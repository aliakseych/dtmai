"use client";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { MockRunner } from "@/components/mocks/MockRunner";
import { RequireAuth } from "@/lib/auth";

/** ?attempt=<id> */
function Run() {
  const id = useSearchParams().get("attempt");
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
