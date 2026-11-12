"use client";
import { useEffect, useId, useRef, useState } from "react";
import { Icon } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { Markdown } from "@/components/temur/Markdown";
import { api } from "@/lib/api";

type Sheet = { content: string; source: string };
type State = { key: string; sheet: Sheet | null | "error" };
const cache = new Map<string, Sheet | null>();

/** Reference sheet for a subject; null while loading or when the subject has none (404). */
function useReference(subjectId: string | null | undefined): Sheet | null | "error" {
  const { locale } = useLocale();
  const key = subjectId ? `${subjectId}:${locale}` : "";
  const [state, setState] = useState<State>({ key: "", sheet: null });
  useEffect(() => {
    if (!subjectId || cache.has(key)) return;
    let live = true;
    api
      .unwrap(api.client.GET("/v1/catalog/subjects/{subject_id}/reference", { params: { path: { subject_id: subjectId }, query: { locale } } }))
      .then((r) => { cache.set(key, { content: r.content, source: r.source }); })
      .catch((e: unknown) => {
        if ((e as { status?: number }).status === 404) cache.set(key, null);
        else if (live) setState({ key, sheet: "error" });
      })
      .finally(() => live && setState((s) => ({ ...s, key })));
    return () => { live = false; };
  }, [subjectId, locale, key]);
  if (!key) return null;
  if (cache.has(key)) return cache.get(key) ?? null;
  return state.key === key && state.sheet === "error" ? "error" : null;
}

/** "Formulas" button + drawer (bottom sheet on phones, side panel on desktop). Renders nothing when the subject has no sheet. */
export function FormulaSheet({ subjectId, className = "" }: { subjectId: string | null | undefined; className?: string }) {
  const t = useT();
  const sheet = useReference(subjectId);
  const [open, setOpen] = useState(false);
  const titleId = useId();
  const panel = useRef<HTMLElement>(null);
  const opener = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement as HTMLElement | null;
    panel.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") { e.stopPropagation(); setOpen(false); return; }
      if (e.key !== "Tab" || !panel.current) return;
      const f = panel.current.querySelectorAll<HTMLElement>("button,[href],[tabindex]:not([tabindex='-1'])");
      if (!f.length) return;
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", onKey, true);
    return () => { document.removeEventListener("keydown", onKey, true); (prev ?? opener.current)?.focus(); };
  }, [open]);

  if (!sheet) return null;
  if (sheet === "error") return null;
  return (
    <>
      <button ref={opener} type="button" onClick={() => setOpen(true)} aria-haspopup="dialog"
        className={`flex h-11 min-w-11 shrink-0 items-center justify-center gap-1.5 rounded-xl border-2 border-line px-2.5 text-sm font-extrabold text-ink-soft hover:bg-snow sm:px-3 ${className}`}>
        <Icon name="learn" size={20} />
        <span className="sr-only sm:not-sr-only">{t("reference.button")}</span>
      </button>
      {open && (
        <div className="fixed inset-0 z-[60] flex items-end justify-end bg-black/40 sm:items-stretch" onMouseDown={(e) => e.target === e.currentTarget && setOpen(false)}>
          <section ref={panel} tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby={titleId}
            className="flex max-h-[85dvh] w-full flex-col rounded-t-3xl bg-white pb-[env(safe-area-inset-bottom)] outline-none sm:max-h-none sm:w-[420px] sm:rounded-none sm:border-l-2 sm:border-line">
            <header className="flex items-center justify-between gap-2 border-b-2 border-line px-4 py-3">
              <h2 id={titleId} className="text-xl font-extrabold">{t("reference.title")}</h2>
              <button type="button" onClick={() => setOpen(false)} aria-label={t("common.close")} className="grid size-11 place-items-center rounded-xl text-ink-soft hover:bg-snow">
                <Icon name="close" size={20} />
              </button>
            </header>
            <div className="formula-sheet min-h-0 flex-1 overflow-y-auto px-4 py-3">
              <Markdown text={sheet.content} />
              {sheet.source && <p className="mt-4 text-xs text-ink-soft">{t("reference.source", { source: sheet.source })}</p>}
            </div>
          </section>
        </div>
      )}
    </>
  );
}
