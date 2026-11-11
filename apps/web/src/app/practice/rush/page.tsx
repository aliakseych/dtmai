"use client";
import { Suspense } from "react";
import { RushView } from "@/components/rush/RushView";
import { RequireAuth } from "@/lib/auth";

export default function RushPage() {
  return (
    <RequireAuth>
      <Suspense>
        <RushView />
      </Suspense>
    </RequireAuth>
  );
}
