"use client";
import { useSearchParams } from "next/navigation";
import { Suspense, useMemo } from "react";
import { LessonPlayer } from "@/components/lesson/LessonPlayer";
import { api } from "@/lib/api";
import { RequireAuth, useLearnLanguage } from "@/lib/auth";
import { pickReviewSubject } from "@/lib/stats";

/** ?kind=review|drill&subject=<id>[&topic=<id>][&type=<id>] */
function Run() {
  const params = useSearchParams();
  const kind = params.get("kind") === "drill" ? "drill" : "review";
  const subject = params.get("subject") ?? "";
  const topic = params.get("topic");
  const type = params.get("type");
  const language = useLearnLanguage();
  const load = useMemo(
    () => async () => {
      let subject_id = subject;
      if (!subject_id && kind === "review") subject_id = (await pickReviewSubject()) ?? "";
      if (!subject_id) subject_id = (await api.unwrap(api.client.GET("/v1/catalog/subjects")))[0]?.id ?? "";
      return kind === "drill"
        ? api.unwrap(api.client.POST("/v1/learning/drills/start", { body: { subject_id, language, count: 10, topic_id: topic, type_id: type } }))
        : api.unwrap(api.client.POST("/v1/learning/review/start", { body: { subject_id, language, count: 10 } }));
    },
    [kind, subject, topic, type, language],
  );
  return <LessonPlayer key={`${kind}|${subject}|${topic}|${type}`} load={load} exitHref="/practice/" />;
}

export default function PracticeRunPage() {
  return (
    <RequireAuth>
      <Suspense>
        <Run />
      </Suspense>
    </RequireAuth>
  );
}
