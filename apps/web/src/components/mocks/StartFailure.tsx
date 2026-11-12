"use client";
import Link from "next/link";
import { ApiError } from "@dtmai/api-client";
import { useT } from "@dtmai/i18n";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";

/** True when starting a mock failed because an unfinished attempt already exists. */
export const isActiveConflict = (e: unknown) => e instanceof ApiError && e.status === 409;

/** Start-failure note; for a 409 it offers to continue the unfinished attempt. */
export function StartFailure({ conflict }: { conflict: boolean }) {
  const t = useT();
  const active = useAsync(async () => (conflict ? api.unwrap(api.client.GET("/v1/assessment/attempts/active")) : null), [conflict]);
  const id = active.state.status === "ready" ? active.state.data?.id : undefined;
  return (
    <p role="alert" className="font-bold text-red-deep">
      {conflict ? t("mock.activeExists") : t("mock.startError")}{" "}
      {conflict && id && (
        <Link href={`/mocks/run/?attempt=${id}`} className="inline-flex min-h-11 items-center text-brand underline">
          {t("mock.resumeBtn")}
        </Link>
      )}
    </p>
  );
}
