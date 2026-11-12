"use client";
import Link from "next/link";
import { ApiError } from "@dtmai/api-client";
import { useT } from "@dtmai/i18n";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";

export type StartFailureKind = "conflict" | "empty" | "failed";

/** Classifies a failed mock start by its API error code (409 alone is ambiguous). */
export function startFailureKind(e: unknown): StartFailureKind {
  if (!(e instanceof ApiError)) return "failed";
  if (e.code === "active_attempt_exists") return "conflict";
  if (e.code === "no_questions" || e.code === "no_questions_personal") return "empty";
  return "failed";
}

/** Start-failure note; for an unfinished-attempt conflict it offers to continue that attempt. */
export function StartFailure({ kind }: { kind: StartFailureKind }) {
  const t = useT();
  const conflict = kind === "conflict";
  const active = useAsync(async () => (conflict ? api.unwrap(api.client.GET("/v1/assessment/attempts/active")) : null), [conflict]);
  const id = active.state.status === "ready" ? active.state.data?.id : undefined;
  return (
    <p role="alert" className="font-bold text-red-deep">
      {conflict ? t("mock.activeExists") : kind === "empty" ? t("mock.noQuestions") : t("mock.startError")}{" "}
      {conflict && id && (
        <Link href={`/mocks/run/?attempt=${id}`} className="inline-flex min-h-11 items-center text-brand underline">
          {t("mock.resumeBtn")}
        </Link>
      )}
    </p>
  );
}
