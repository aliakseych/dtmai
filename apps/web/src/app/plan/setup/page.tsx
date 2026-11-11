"use client";
import { RequireAuth } from "@/lib/auth";
import { PlanWizard } from "@/components/planner/PlanWizard";

export default function PlanSetupPage() {
  return (
    <RequireAuth>
      <PlanWizard />
    </RequireAuth>
  );
}
