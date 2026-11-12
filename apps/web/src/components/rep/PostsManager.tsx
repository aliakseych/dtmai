"use client";
import { useState } from "react";
import { Button, Card, ConfirmModal, cn } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import type { MessageKey } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { useAsync } from "@/lib/useAsync";
import { PostForm } from "./PostForm";
import { KIND_LABEL, rep, type PostKind, type RepPost } from "./repApi";
import { repErrorKey } from "./repErrors";

const STATUS: Record<string, { label: MessageKey; tone: string }> = {
  draft: { label: "rep.post.status.draft", tone: "bg-snow text-ink-soft" },
  pending: { label: "rep.post.status.pending", tone: "bg-accent-soft text-accent-ink" },
  published: { label: "rep.post.status.published", tone: "bg-brand-soft text-brand" },
  rejected: { label: "rep.post.status.rejected", tone: "bg-red-soft text-red-deep" },
};

export function PostsManager({ lyceumId }: { lyceumId: string }) {
  const t = useT();
  const { locale } = useLocale();
  const { state, reload } = useAsync(() => rep.posts(lyceumId), [lyceumId]);
  const [editing, setEditing] = useState<RepPost | "new" | null>(null);
  const [removing, setRemoving] = useState<RepPost | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const when = (iso: string) => new Date(iso).toLocaleString(locale === "uz-Latn" ? "uz-Latn-UZ" : locale === "uz-Cyrl" ? "uz-Cyrl-UZ" : locale, { dateStyle: "medium", timeStyle: "short" });

  const confirmRemove = async () => {
    if (!removing) return;
    try {
      await rep.remove(lyceumId, removing.id);
      setErr(null);
      reload();
    } catch (e) {
      setErr(t(repErrorKey(e)));
    }
    setRemoving(null);
  };

  if (editing)
    return (
      <PostForm
        lyceumId={lyceumId}
        post={editing === "new" ? null : editing}
        onCancel={() => setEditing(null)}
        onDone={() => {
          setEditing(null);
          reload();
        }}
      />
    );

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-xl text-ink">{t("rep.posts.title")}</h2>
        <Button onClick={() => setEditing("new")}>{t("rep.post.new")}</Button>
      </div>
      {err && <p role="alert" className="text-sm font-bold text-red-deep">{err}</p>}
      <AsyncView state={state} onRetry={reload} isEmpty={(d) => d.length === 0} emptyText={t("rep.posts.empty")}>
        {(posts) => (
          <ul className="flex flex-col gap-3">
            {posts.map((p) => {
              const s = STATUS[p.status] ?? STATUS.draft;
              return (
                <li key={p.id}>
                  <Card>
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <span className={cn("rounded-full px-3 py-1 text-xs font-extrabold uppercase", s.tone)}>{t(s.label)}</span>
                      <span className="text-sm font-bold text-ink-soft">{KIND_LABEL[p.kind as PostKind] ? t(KIND_LABEL[p.kind as PostKind]) : p.kind}</span>
                    </div>
                    <h3 className="break-words text-lg text-ink">{p.title}</h3>
                    {p.body && <p className="mt-1 whitespace-pre-wrap break-words text-ink-soft">{p.body}</p>}
                    {p.starts_at && <p className="mt-1 text-sm text-ink">{t("rep.post.startsAt")}: {when(p.starts_at)}</p>}
                    {p.link && (
                      <a href={p.link} target="_blank" rel="noopener noreferrer" className="mt-1 block break-all text-sm font-bold text-brand underline">
                        {p.link}
                      </a>
                    )}
                    {p.status === "rejected" && p.reject_reason && (
                      <p className="mt-2 rounded-xl bg-red-soft px-3 py-2 text-sm text-red-deep">
                        <span className="font-extrabold">{t("rep.post.reason")}:</span> {p.reject_reason}
                      </p>
                    )}
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button variant="secondary" onClick={() => setEditing(p)}>{t("rep.post.edit")}</Button>
                      <Button variant="ghost" onClick={() => setRemoving(p)}>{t("rep.post.delete")}</Button>
                    </div>
                  </Card>
                </li>
              );
            })}
          </ul>
        )}
      </AsyncView>
      <ConfirmModal
        open={!!removing}
        danger
        title={t("rep.post.deleteTitle")}
        message={removing?.title}
        confirmLabel={t("rep.post.delete")}
        cancelLabel={t("rep.post.cancel")}
        onConfirm={() => void confirmRemove()}
        onClose={() => setRemoving(null)}
      />
    </div>
  );
}
