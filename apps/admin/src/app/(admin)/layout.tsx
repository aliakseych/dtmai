import type { ReactNode } from "react";
import { RequireAdmin } from "@/lib/auth";
import { Shell } from "@/components/Shell";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <RequireAdmin>
      <Shell>{children}</Shell>
    </RequireAdmin>
  );
}
