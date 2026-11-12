"use client";
import { useT } from "@/lib/i18n";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { lyceums, type Post } from "@/lib/lyceums";
import { useAct } from "@/lib/catalog";
import { fmtDate, nm } from "@/lib/util";
import { Badge, Btn, Field, Textarea } from "@/components/ui/controls";
import { Dialog } from "@/components/ui/overlay";
import { DataTable } from "@/components/ui/table";

const KEY = [["lyceum-pending-posts"]] as const;

export function PostModeration() {
  const t = useT();
  const posts = useQuery({ queryKey: KEY[0], queryFn: () => lyceums.posts("pending") });
  const names = useQuery({ queryKey: ["lyceum-list", ""], queryFn: () => lyceums.list("") });
  const label = (id: string) => nm(names.data?.find((l) => l.id === id)?.names, id);
  const [rejecting, setRejecting] = useState<Post | null>(null);
  const [reason, setReason] = useState("");
  const act = useAct((a: { id: string; action: "publish" | "reject"; reason?: string }) => lyceums.moderate(a.id, a.action, a.reason), KEY, t("admin.lyceums.postModerated"));
  const close = () => { setRejecting(null); setReason(""); };
  return (
    <div className="min-h-0 flex-1 overflow-auto">
      <DataTable rows={posts.data} loading={posts.isLoading} error={posts.error} rowKey={(r) => r.id} empty={t("admin.lyceums.noPostsAwaitingModeration")}
        cols={[
          { key: "l", head: t("admin.lyceums.lyceum"), cell: (r) => label(r.lyceum_id) },
          { key: "k", head: t("admin.common.kind"), cell: (r) => <Badge tone="blue">{r.kind}</Badge> },
          { key: "t", head: t("admin.lyceums.post"), className: "max-w-lg", cell: (r) => (
            <div>
              <div className="font-extrabold">{r.title}</div>
              <div className="whitespace-pre-wrap text-ink-soft">{r.body}</div>
              {r.starts_at && <div className="text-xs">{t("admin.lyceums.starts", { date: fmtDate(r.starts_at) })}</div>}
              {r.link && <a href={r.link} target="_blank" rel="noopener noreferrer" className="break-all text-xs text-blue-deep underline">{r.link}</a>}
            </div>
          ) },
          { key: "d", head: t("admin.lyceums.submitted"), cell: (r) => fmtDate(r.created_at) },
          { key: "a", head: "", cell: (r) => (
            <div className="flex gap-1.5">
              <Btn variant="primary" disabled={act.isPending} onClick={() => act.mutate({ id: r.id, action: "publish" })}>{t("admin.common.publish")}</Btn>
              <Btn variant="danger" disabled={act.isPending} onClick={() => setRejecting(r)}>{t("admin.lyceums.reject")}</Btn>
            </div>
          ) },
        ]} />
      <Dialog open={!!rejecting} onClose={close} title={t("admin.lyceums.rejectPost")}
        footer={<><Btn onClick={close}>{t("admin.common.cancel")}</Btn>
          <Btn variant="danger" disabled={!reason.trim() || act.isPending}
            onClick={() => rejecting && act.mutate({ id: rejecting.id, action: "reject", reason: reason.trim() }, { onSuccess: close })}>{t("admin.lyceums.reject")}</Btn></>}>
        <Field label={t("admin.lyceums.reason")} hint={t("admin.lyceums.shownToTheRepresentative")}><Textarea className="font-sans" value={reason} onChange={(e) => setReason(e.target.value)} /></Field>
      </Dialog>
    </div>
  );
}
