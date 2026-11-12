"use client";
import { useT } from "@dtmai/i18n";
import type { SaveState } from "./useAutosave";

export function SaveIndicator({ state, onRetry }: { state: SaveState; onRetry: () => void }) {
  const t = useT();
  if (state === "idle") return <span className="hidden min-w-20 sm:block" />;
  const label = state === "saving" ? t("mock.saving") : state === "saved" ? t("mock.saved") : t("mock.saveError");
  return (
    <span role="status" className={`flex items-center gap-2 text-sm font-bold ${state === "error" ? "text-red-deep" : "text-ink-soft"}`}>
      <span className="sr-only sm:not-sr-only">{label}</span>
      {state === "error" && (
        <button type="button" onClick={onRetry} className="rounded-lg border-2 border-red px-2 py-0.5 text-red-deep">
          {t("mock.retry")}
        </button>
      )}
    </span>
  );
}
