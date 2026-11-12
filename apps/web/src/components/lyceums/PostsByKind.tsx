"use client";
import { useLocale, useT } from "@dtmai/i18n";
import { formatDateTime } from "@/lib/planDates";
import type { LyceumDetailData } from "./useLyceumDetail";

type Post = LyceumDetailData["posts"][number];

/** Display order of post kinds; unknown kinds from the API are appended after these. */
export const POST_KINDS = ["announcement", "offer", "free_mock", "visit", "event", "alumni", "chat_link", "faculty"] as const;

const safeLink = (l: string | null) => (l && /^(https?:\/\/|tg:\/\/)/i.test(l) ? l : null);

function PostItem({ post }: { post: Post }) {
  const t = useT();
  const { locale } = useLocale();
  const link = safeLink(post.link);
  const when = post.starts_at ? formatDateTime(post.starts_at, locale) : null;
  return (
    <li className="rounded-2xl border-2 border-line p-3">
      <h4 className="break-words font-bold text-ink">{post.title}</h4>
      {when && <p className="text-sm font-bold text-brand">{when}</p>}
      {post.body && <p className="mt-1 whitespace-pre-line break-words text-ink-soft">{post.body}</p>}
      {link && (
        <a href={link} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block break-all font-bold text-brand underline">
          {t("lyceums.post.open")}
        </a>
      )}
    </li>
  );
}

export function PostsByKind({ posts }: { posts: Post[] }) {
  const t = useT();
  const kinds = [...POST_KINDS, ...Array.from(new Set(posts.map((p) => p.kind))).filter((k) => !(POST_KINDS as readonly string[]).includes(k))];
  const groups = kinds.map((k) => ({ kind: k, items: posts.filter((p) => p.kind === k) })).filter((g) => g.items.length > 0);
  if (groups.length === 0) return null;
  return (
    <section className="flex flex-col gap-4">
      {groups.map((g) => (
        <div key={g.kind}>
          <h3 className="mb-2 text-lg font-extrabold text-ink">{t(`lyceums.kind.${g.kind}` as never)}</h3>
          <ul className="flex flex-col gap-2">
            {g.items.map((p) => (
              <PostItem key={p.id} post={p} />
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}
