"use client";
import { useState } from "react";
import { Button, Card } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { KIND_LABEL, NEEDS_LINK, NEEDS_START, POST_KINDS, rep, type PostKind, type RepPost } from "./repApi";
import { repErrorKey } from "./repErrors";

const field = "w-full rounded-2xl border-2 border-line bg-snow px-4 py-3 text-ink focus:border-brand focus:bg-white";

/** ISO instant → value for <input type="datetime-local"> (local time). */
const toLocalInput = (iso: string | null) => {
  if (!iso) return "";
  const d = new Date(iso);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
};

export function PostForm({ lyceumId, post, onDone, onCancel }: { lyceumId: string; post: RepPost | null; onDone: () => void; onCancel: () => void }) {
  const t = useT();
  const [kind, setKind] = useState<string>(post?.kind ?? POST_KINDS[0]);
  const [title, setTitle] = useState(post?.title ?? "");
  const [body, setBody] = useState(post?.body ?? "");
  const [startsAt, setStartsAt] = useState(toLocalInput(post?.starts_at ?? null));
  const [link, setLink] = useState(post?.link ?? "");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const scheduled = NEEDS_START.includes(kind);
  const linked = NEEDS_LINK.includes(kind);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    const payload = {
      kind,
      title: title.trim(),
      body: body.trim(),
      starts_at: startsAt ? new Date(startsAt).toISOString() : null,
      link: link.trim() || null,
    };
    try {
      if (post) await rep.update(lyceumId, post.id, payload);
      else await rep.create(lyceumId, payload);
      onDone();
    } catch (e2) {
      setErr(t(repErrorKey(e2)));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card>
      <form onSubmit={submit} className="flex flex-col gap-3">
        <h2 className="text-xl text-ink">{post ? t("rep.post.edit") : t("rep.post.new")}</h2>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-bold text-ink-soft">{t("rep.post.kind")}</span>
          <select value={kind} onChange={(e) => setKind(e.target.value)} className={field}>
            {POST_KINDS.map((k: PostKind) => (
              <option key={k} value={k}>{t(KIND_LABEL[k])}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-bold text-ink-soft">{t("rep.post.title")}</span>
          <input required maxLength={200} value={title} onChange={(e) => setTitle(e.target.value)} className={field} />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-bold text-ink-soft">{t("rep.post.body")}</span>
          <textarea rows={5} value={body} onChange={(e) => setBody(e.target.value)} className={field} />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-bold text-ink-soft">
            {t("rep.post.startsAt")} {scheduled ? "*" : `(${t("rep.post.optional")})`}
          </span>
          <input type="datetime-local" required={scheduled} value={startsAt} onChange={(e) => setStartsAt(e.target.value)} className={field} />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-bold text-ink-soft">
            {t("rep.post.link")} {linked ? "*" : `(${t("rep.post.optional")})`}
          </span>
          <input type="url" required={linked} value={link} onChange={(e) => setLink(e.target.value)} placeholder="https://" className={field} />
        </label>
        {post?.status === "published" && <p className="text-sm text-ink-soft">{t("rep.post.reviewNote")}</p>}
        {err && <p role="alert" className="text-sm font-bold text-red-deep">{err}</p>}
        <div className="flex flex-wrap gap-2">
          <Button type="submit" disabled={busy || !title.trim()}>{t("rep.post.save")}</Button>
          <Button variant="secondary" onClick={onCancel}>{t("rep.post.cancel")}</Button>
        </div>
      </form>
    </Card>
  );
}
