import type { ReactNode } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { RequireAuth } from "@/lib/auth";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <RequireAuth>
      <AppShell>{children}</AppShell>
    </RequireAuth>
  );
}
