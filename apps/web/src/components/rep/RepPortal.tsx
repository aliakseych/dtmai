"use client";
import { useState } from "react";
import { ApiError } from "@dtmai/api-client";
import { Button, Card } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { PageTitle } from "@/components/PageTitle";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";
import { ApplyForm } from "./ApplyForm";
import { PostsManager } from "./PostsManager";
import { rep, type Membership } from "./repApi";

/** `null` = the user has never applied to this lyceum (API answers 404). */
async function loadMembership(id: string): Promise<Membership | null> {
  try {
    return await rep.membership(id);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}

function LyceumRep({ lyceumId }: { lyceumId: string }) {
  const t = useT();
  const { state, reload } = useAsync(() => loadMembership(lyceumId), [lyceumId]);
  return (
    <AsyncView state={state} onRetry={reload}>
      {(m) => {
        if (m?.status === "approved") return <PostsManager lyceumId={lyceumId} />;
        if (m?.status === "pending")
          return (
            <Card>
              <h2 className="text-xl text-ink">{t("rep.status.pendingTitle")}</h2>
              <p className="mt-1 text-ink-soft">{t("rep.status.pending")}</p>
            </Card>
          );
        return <ApplyForm lyceumId={lyceumId} rejected={m?.status === "rejected"} onApplied={reload} />;
      }}
    </AsyncView>
  );
}

export function RepPortal() {
  const t = useT();
  const { locale } = useLocale();
  const { isGuest } = useAuth();
  const [q, setQ] = useState("");
  const [lyceumId, setLyceumId] = useState<string | null>(null);
  const { state, reload } = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums", { params: { query: { q: q || undefined } } })), [q]);

  return (
    <>
      <PageTitle>{t("rep.title")}</PageTitle>
      {isGuest && <p role="alert" className="mb-4 text-sm font-bold text-red-deep">{t("rep.err.guest_cannot_apply")}</p>}
      {lyceumId ? (
        <div className="flex flex-col gap-4">
          <div>
            <Button variant="ghost" onClick={() => setLyceumId(null)}>← {t("rep.change")}</Button>
          </div>
          <LyceumRep lyceumId={lyceumId} />
        </div>
      ) : (
        <>
          <p className="mb-3 text-ink-soft">{t("rep.pick")}</p>
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t("lyceums.search")}
            aria-label={t("lyceums.search")}
            className="mb-4 w-full rounded-2xl border-2 border-line bg-snow px-4 py-3 text-ink focus:border-blue focus:bg-white"
          />
          <AsyncView state={state} onRetry={reload} isEmpty={(d) => d.length === 0} emptyText={t("lyceums.none")}>
            {(list) => (
              <ul className="flex flex-col gap-2">
                {list.map((l) => (
                  <li key={l.id}>
                    <button
                      type="button"
                      onClick={() => setLyceumId(l.id)}
                      className="w-full break-words rounded-2xl border-2 border-line bg-white px-4 py-3 text-left text-lg text-ink transition hover:bg-snow active:scale-[0.99]"
                    >
                      {pick(l.names, locale)}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </AsyncView>
        </>
      )}
    </>
  );
}
