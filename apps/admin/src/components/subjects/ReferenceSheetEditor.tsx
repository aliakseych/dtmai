"use client";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useT } from "@/lib/i18n";
import { catalog, qk, useAct, type Subject } from "@/lib/catalog";
import { LOCALE_LIST, nm } from "@/lib/util";
import { Btn, Check, Field, Input, Textarea } from "@/components/ui/controls";
import { Drawer } from "@/components/ui/overlay";
import { useConfirm } from "@/components/ui/confirm";
import { Md } from "@/components/ui/markdown";

/** Per-subject formula/reference sheet shown to learners in lessons and mocks. Markdown + $LaTeX$, one body per locale. */
export function ReferenceSheetEditor({ subject, onClose }: { subject: Subject | null; onClose: () => void }) {
  const t = useT();
  const [ask, confirmNode] = useConfirm();
  const id = subject?.id ?? "";
  const q = useQuery({ queryKey: qk.reference(id), queryFn: () => catalog.reference.get(id), enabled: !!id });
  const [contents, setContents] = useState<Record<string, string>>({});
  const [source, setSource] = useState("");
  const [active, setActive] = useState(true);
  const [loc, setLoc] = useState<string>(LOCALE_LIST[0]);
  useEffect(() => {
    if (!q.isSuccess) return;
    setContents({ ...(q.data?.contents ?? {}) });
    setSource(q.data?.source ?? "");
    setActive(q.data?.active ?? true);
  }, [q.isSuccess, q.data]);
  const save = useAct(
    () => catalog.reference.put(id, { contents: Object.fromEntries(Object.entries(contents).filter(([, v]) => v.trim())), source: source.trim(), active }),
    [qk.reference(id)],
    t("admin.common.saved"),
  );
  const del = useAct(() => catalog.reference.remove(id), [qk.reference(id)], t("admin.common.deleted"));
  const hasAny = Object.values(contents).some((v) => v.trim());
  return (
    <>
      <Drawer open={!!subject} onClose={onClose} width="max-w-4xl" title={t("admin.reference.title", { name: subject ? nm(subject.names) || subject.code : "" })}
        footer={<>
          {q.data && <Btn variant="danger" className="mr-auto" disabled={del.isPending} onClick={() => ask({ title: t("admin.reference.deleteConfirm"), name: subject?.code ?? "", danger: true, confirmLabel: t("admin.common.delete") }, () => del.mutate(undefined, { onSuccess: () => { setContents({}); setSource(""); } }))}>{t("admin.common.delete")}</Btn>}
          <Btn onClick={onClose}>{t("admin.common.cancel")}</Btn>
          <Btn variant="primary" disabled={save.isPending || !hasAny} onClick={() => save.mutate(undefined, { onSuccess: onClose })}>{t("admin.common.save")}</Btn>
        </>}>
        {q.isLoading ? <p className="text-sm text-ink-soft">{t("admin.common.loading")}</p>
          : q.isError ? <p role="alert" className="text-sm font-bold text-red-deep">{t("admin.reference.loadError")}</p>
          : (
            <div className="space-y-3">
              {!q.data && <p className="text-sm text-ink-soft">{t("admin.reference.empty")}</p>}
              <div role="tablist" className="flex flex-wrap gap-1">
                {LOCALE_LIST.map((l) => (
                  <button key={l} type="button" role="tab" aria-selected={loc === l} onClick={() => setLoc(l)}
                    className={`rounded-xl border px-3 py-1.5 text-xs font-extrabold ${loc === l ? "border-ink bg-ink text-white" : "border-line bg-white"}`}>
                    {l}{contents[l]?.trim() ? " ●" : ""}
                  </button>
                ))}
              </div>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                <Field label={t("admin.reference.bodyMarkdownLatex")}><Textarea rows={22} value={contents[loc] ?? ""} onChange={(e) => setContents({ ...contents, [loc]: e.target.value })} /></Field>
                <div className="rounded-xl border border-line bg-snow p-2"><div className="mb-1 text-xs font-extrabold uppercase text-ink-soft">{t("admin.common.preview")}</div><Md text={contents[loc] || "…"} /></div>
              </div>
              <Field label={t("admin.reference.source")} hint={t("admin.reference.sourceHint")}><Input value={source} maxLength={500} onChange={(e) => setSource(e.target.value)} /></Field>
              <Check checked={active} onChange={setActive} label={t("admin.reference.visible")} />
            </div>
          )}
      </Drawer>
      {confirmNode}
    </>
  );
}
