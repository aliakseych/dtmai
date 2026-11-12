"use client";
import { Suspense } from "react";
import { RegisterForm } from "@/components/auth/RegisterForm";
import { RequireAuth } from "@/lib/auth";

/** Mandatory account step after the study plan: email + password or Google; existing users follow the login link. */
export default function AccountPage() {
  return (
    <RequireAuth allowUnonboarded>
      <Suspense>
        <RegisterForm gate />
      </Suspense>
    </RequireAuth>
  );
}
