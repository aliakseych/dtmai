"use client";
import { usePathname } from "next/navigation";
import { Suspense, useMemo } from "react";
import { LessonPlayer } from "@/components/lesson/LessonPlayer";
import { api } from "@/lib/api";
import { RequireAuth, useLearnLanguage } from "@/lib/auth";

function Run({ id }: { id: string }) {
  const language = useLearnLanguage();
  const load = useMemo(() => () => api.unwrap(api.client.POST("/v1/learning/lessons/start", { body: { lesson_id: id, language } })), [id, language]);
  return <LessonPlayer load={load} exitHref="/learn/" lessonId={id} />;
}

export function LessonRoute() {
  const id = usePathname().split("/").filter(Boolean)[1] ?? "";
  return (
    <RequireAuth>
      <Suspense>
        <Run id={id} />
      </Suspense>
    </RequireAuth>
  );
}
