"use client";
import { ConfirmModal } from "@dtmai/ui";
import { useCallback, useState, type ReactNode } from "react";
import { useT } from "@/lib/i18n";

export interface ConfirmOpts {
  /** The question, e.g. "Delete this subject?". */
  title: string;
  /** Name of the entity acted on, shown in bold under the title. */
  name?: string;
  /** Extra consequence text. */
  body?: ReactNode;
  /** Confirm button label; defaults to a generic "Confirm". */
  confirmLabel?: string;
  /** Cancel button label; defaults to a generic "Cancel". */
  cancelLabel?: string;
  danger?: boolean;
}

/** Replacement for window.confirm(): `const [ask, node] = useConfirm(); ask({title, name}, () => run())` and render `{node}`. */
export function useConfirm(): [(o: ConfirmOpts, onYes: () => void) => void, ReactNode] {
  const t = useT();
  const [s, setS] = useState<{ o: ConfirmOpts; yes: () => void } | null>(null);
  const ask = useCallback((o: ConfirmOpts, yes: () => void) => setS({ o, yes }), []);
  const node = (
    <ConfirmModal
      open={!!s}
      title={s?.o.title ?? ""}
      message={s && (s.o.name || s.o.body) ? <>{s.o.name && <p className="break-words font-bold text-ink">{s.o.name}</p>}{s.o.body}</> : undefined}
      confirmLabel={s?.o.confirmLabel ?? t("admin.common.confirm")}
      cancelLabel={s?.o.cancelLabel ?? t("admin.common.cancel")}
      danger={s?.o.danger}
      onConfirm={() => { const y = s?.yes; setS(null); y?.(); }}
      onClose={() => setS(null)}
    />
  );
  return [ask, node];
}
