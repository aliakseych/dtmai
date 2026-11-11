import type { ReactNode } from "react";
import { RequireAdmin } from "@/lib/auth";

export default function LabelingLayout({ children }: { children: ReactNode }) {
  return <RequireAdmin>{children}</RequireAdmin>;
}
