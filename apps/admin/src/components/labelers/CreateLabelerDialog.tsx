"use client";
import { useState } from "react";
import { Btn, Field, Input } from "@/components/ui/controls";
import { Dialog } from "@/components/ui/overlay";
import { labelers, type LabelerCreated } from "@/lib/labelers";
import { useUserAct } from "@/lib/users";
import { useToast } from "@dtmai/ui";

function Secret({ label, value }: { label: string; value: string }) {
  const toast = useToast();
  return (
    <div>
      <div className="mb-0.5 text-[11px] font-extrabold uppercase tracking-wide text-ink-soft">{label}</div>
      <div className="flex items-center gap-2">
        <code className="min-w-0 flex-1 select-all break-all rounded-md border border-line bg-snow px-2 py-1.5 text-[13px]">{value}</code>
        <Btn onClick={() => navigator.clipboard.writeText(value).then(() => toast("Copied", "success"), () => toast("Copy failed", "error"))}>Copy</Btn>
      </div>
    </div>
  );
}

/** Creates a system labeler; the generated credentials are shown once and dropped on close. */
export function CreateLabelerDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [name, setName] = useState("");
  const [created, setCreated] = useState<LabelerCreated | null>(null);
  const create = useUserAct((n: string) => labelers.create(n.trim()), [["admin-users"]]);
  const close = () => { setName(""); setCreated(null); onClose(); };
  return (
    <Dialog open={open} onClose={close} dismissable={!created && !create.isPending} title={created ? "Labeler created" : "Create system labeler"}
      footer={created ? <Btn variant="primary" onClick={close}>I saved the credentials</Btn> : <><Btn onClick={close}>Cancel</Btn><Btn variant="primary" disabled={create.isPending} onClick={() => create.mutate(name, { onSuccess: setCreated })}>Create</Btn></>}>
      {created ? (
        <div className="space-y-3">
          <p role="alert" className="rounded-md border border-gold bg-yellow-50 px-3 py-2 text-xs font-bold text-gold-deep">The password is shown only once and can't be retrieved later. Copy it now.</p>
          <Secret label="Login" value={created.login} />
          <Secret label="Password" value={created.password} />
        </div>
      ) : (
        <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); if (!create.isPending) create.mutate(name, { onSuccess: setCreated }); }}>
          <Field label="Display name" hint="Optional. Login and password are generated for you."><Input value={name} onChange={(e) => setName(e.target.value)} /></Field>
        </form>
      )}
    </Dialog>
  );
}
