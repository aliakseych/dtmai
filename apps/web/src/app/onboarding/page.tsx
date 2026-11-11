"use client";
import { RequireAuth } from "@/lib/auth";
import { Onboarding } from "@/components/onboarding/Onboarding";

export default function OnboardingPage() {
  return (
    <RequireAuth allowUnonboarded>
      <Onboarding />
    </RequireAuth>
  );
}
