import { Suspense } from "react";
import { LyceumPage } from "@/components/lyceums/LyceumPage";

export default function LyceumRoute() {
  return (
    <Suspense>
      <LyceumPage />
    </Suspense>
  );
}
