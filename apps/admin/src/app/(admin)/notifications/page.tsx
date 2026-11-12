"use client";
import { useT } from "@/lib/i18n";
import { useState } from "react";
import { notifications, type BroadcastIn } from "@/lib/notifications";
import { useAct } from "@/lib/catalog";
import { Btn, Field, Input, PageHeader, Select, Textarea } from "@/components/ui/controls";
import { LangInput } from "@/components/ui/lang";
import { useConfirm } from "@/components/ui/confirm";

export default function NotificationsPage() {
  const t = useT();
  const [ask, confirmNode] = useConfirm();
  const [f, setF] = useState<BroadcastIn>({ channel: "telegram", locale: null, title: "", body: "", dry_run: true });
  const send = useAct((b: BroadcastIn) => notifications.broadcast(b), [], undefined);
  const set = (p: Partial<BroadcastIn>) => setF((x) => ({ ...x, ...p }));
  return (
    <>
      <PageHeader title={t("admin.notifications.notifications")} sub={t("admin.notifications.broadcastAnAnnouncementTo")} />
      <div className="max-w-2xl space-y-3 p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Field label={t("admin.notifications.channel")}><Select value={f.channel} onChange={(e) => set({ channel: e.target.value as BroadcastIn["channel"] })}><option value="telegram">{t("admin.notifications.telegram")}</option><option value="email">{t("admin.notifications.email")}</option><option value="push">{t("admin.notifications.push")}</option></Select></Field>
          <Field label={t("admin.notifications.localeBlankAll")}><LangInput value={f.locale ?? ""} onChange={(v) => set({ locale: v || null })} /></Field>
        </div>
        <Field label={t("admin.common.title")}><Input value={f.title} onChange={(e) => set({ title: e.target.value })} /></Field>
        <Field label={t("admin.notifications.message")}><Textarea rows={5} value={f.body} onChange={(e) => set({ body: e.target.value })} /></Field>
        <div className="flex items-center gap-3">
          <Btn disabled={!f.title || !f.body || send.isPending} onClick={() => send.mutate({ ...f, dry_run: true })}>{t("admin.notifications.previewRecipients")}</Btn>
          <Btn variant="primary" disabled={!f.title || !f.body || send.isPending} onClick={() => ask({ title: t("admin.notifications.sendToAllMatching"), name: f.title, confirmLabel: t("admin.notifications.send") }, () => send.mutate({ ...f, dry_run: false }))}>{t("admin.notifications.send")}</Btn>
          {send.data && <span className="text-sm">{t("admin.notifications.recipients", { n: send.data.recipients })}{send.data.queued ? t("admin.notifications.queued") : t("admin.notifications.preview")}</span>}
        </div>
      </div>
      {confirmNode}
    </>
  );
}
