"use client";
import type { ReactNode } from "react";
import Link from "next/link";
import { ApiError } from "@dtmai/api-client";
import { Button, buttonClass, Mascot, Skeleton } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import type { AsyncState } from "@/lib/useAsync";

export function AsyncView<T>({
  state,
  onRetry,
  isEmpty,
  emptyText,
  exitHref = "/",
  children,
}: {
  state: AsyncState<T>;
  onRetry: () => void;
  isEmpty?: (data: T) => boolean;
  emptyText?: string;
  /** Where the error screen's exit link goes (a lesson/run exits to its hub, not the landing page). */
  exitHref?: string;
  children: (data: T) => ReactNode;
}) {
  const t = useT();
  if (state.status === "loading")
    return (
      <div className="flex flex-col items-center gap-3" aria-busy="true" aria-label={t("common.loading")}>
        <Mascot mood="thinking" size={96} alt="" className="h-auto w-20" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  if (state.status === "error") {
    const offline = state.kind === "offline";
    const auth = state.kind === "auth";
    const code = state.error instanceof ApiError ? state.error.code : undefined;
    const mapped = code === "no_questions" || code === "no_questions_personal" ? t("err.noQuestions") : code === "lesson_locked" ? t("err.lessonLocked") : code === "conflict" ? t("err.conflict") : null;
    return (
      <div role="alert" className="flex flex-col items-center gap-3 py-10 text-center">
        <Mascot mood={offline ? "sleep" : "sad"} size={120} alt="" className="h-auto w-24" />
        <p className="text-ink-soft">{offline ? t("common.offline") : auth ? t("common.sessionExpired") : (mapped ?? t("common.error"))}</p>
        {auth ? (
          <Link href="/login/" className={buttonClass("primary")}>
            {t("auth.login.cta")}
          </Link>
        ) : (
          <>
            {!mapped && (
              <Button variant="secondary" onClick={onRetry}>
                {t("common.retry")}
              </Button>
            )}
            <Link href={exitHref} className={buttonClass(mapped ? "primary" : "ghost")}>
              {t("nav.home")}
            </Link>
          </>
        )}
      </div>
    );
  }
  if (isEmpty?.(state.data))
    return (
      <div className="flex flex-col items-center gap-2 py-10 text-center">
        <Mascot mood="point" size={96} alt="" className="h-auto w-20" />
        <p className="text-ink-soft">{emptyText ?? t("common.empty")}</p>
      </div>
    );
  return <>{children(state.data)}</>;
}
