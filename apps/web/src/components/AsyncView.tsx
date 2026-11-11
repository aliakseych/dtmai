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
  children,
}: {
  state: AsyncState<T>;
  onRetry: () => void;
  isEmpty?: (data: T) => boolean;
  emptyText?: string;
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
    const title = state.error instanceof ApiError ? state.error.problem?.title : undefined;
    return (
      <div role="alert" className="flex flex-col items-center gap-3 py-10 text-center">
        <Mascot mood={offline ? "sleep" : "sad"} size={120} alt="" className="h-auto w-24" />
        <p className="text-ink-soft">{offline ? t("common.offline") : auth ? t("common.sessionExpired") : t("common.error")}</p>
        {!offline && !auth && title && <p className="text-sm font-bold text-ink-soft">{title}</p>}
        {auth ? (
          <Link href="/login/" className={buttonClass("primary")}>
            {t("auth.login.cta")}
          </Link>
        ) : (
          <Button variant="secondary" onClick={onRetry}>
            {t("common.retry")}
          </Button>
        )}
      </div>
    );
  }
  if (isEmpty?.(state.data))
    return (
      <div className="flex flex-col items-center gap-2 py-10 text-center">
        <Mascot mood="thinking" size={96} alt="" className="h-auto w-20" />
        <p className="text-ink-soft">{emptyText ?? t("common.empty")}</p>
      </div>
    );
  return <>{children(state.data)}</>;
}
