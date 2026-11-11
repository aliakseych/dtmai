"use client";
import { useState } from "react";
import { notifications, type BroadcastIn } from "@/lib/notifications";
import { useAct } from "@/lib/catalog";
import { Btn, Field, Input, PageHeader, Select, Textarea } from "@/components/ui/controls";
import { LangInput } from "@/components/ui/lang";

export default function NotificationsPage() {
  const [f, setF] = useState<BroadcastIn>({ channel: "telegram", locale: null, title: "", body: "", dry_run: true });
  const send = useAct((b: BroadcastIn) => notifications.broadcast(b), [], undefined);
  const set = (p: Partial<BroadcastIn>) => setF((x) => ({ ...x, ...p }));
  return (
    <>
      <PageHeader title="Notifications" sub="Broadcast an announcement to all users of a channel and locale. Always preview recipients first." />
      <div className="max-w-2xl space-y-3 p-4">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Channel"><Select value={f.channel} onChange={(e) => set({ channel: e.target.value as BroadcastIn["channel"] })}><option>telegram</option><option>email</option><option>push</option></Select></Field>
          <Field label="Locale (blank = all)"><LangInput value={f.locale ?? ""} onChange={(v) => set({ locale: v || null })} /></Field>
        </div>
        <Field label="Title"><Input value={f.title} onChange={(e) => set({ title: e.target.value })} /></Field>
        <Field label="Message"><Textarea rows={5} value={f.body} onChange={(e) => set({ body: e.target.value })} /></Field>
        <div className="flex items-center gap-3">
          <Btn disabled={!f.title || !f.body || send.isPending} onClick={() => send.mutate({ ...f, dry_run: true })}>Preview recipients</Btn>
          <Btn variant="primary" disabled={!f.title || !f.body || send.isPending} onClick={() => confirm("Send to all matching users?") && send.mutate({ ...f, dry_run: false })}>Send</Btn>
          {send.data && <span className="text-sm">{send.data.recipients} recipients{send.data.queued ? " — queued" : " (preview)"}</span>}
        </div>
      </div>
    </>
  );
}
