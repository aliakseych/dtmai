"use client";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { MockResult } from "@/components/mocks/MockResult";
import { RequireAuth } from "@/lib/auth";

/** ?attempt=<id> */
function Result() {
  const id = useSearchParams().get("attempt");
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
