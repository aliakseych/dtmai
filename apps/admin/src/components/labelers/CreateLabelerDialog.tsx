"use client";
import { useT } from "@/lib/i18n";
import { useState } from "react";
import { Btn, Field, Input } from "@/components/ui/controls";
import { Dialog } from "@/components/ui/overlay";
import { labelers, type LabelerCreated } from "@/lib/labelers";
import { useUserAct } from "@/lib/users";
import { useToast } from "@dtmai/ui";

function Secret({ label, value }: { label: string; value: string }) {
  const t = useT();
  const toast = useToast();
  return (
    <div>
      <div className="mb-0.5 text-xs font-extrabold uppercase tracking-wide text-ink-soft">{label}</div>
      <div className="flex items-center gap-2">
        <code className="min-w-0 flex-1 select-all break-all rounded-xl border border-line bg-snow px-2 py-1.5 text-sm">{value}</code>
        <Btn onClick={() => navigator.clipboard.writeText(value).then(() => toast(t("admin.common.copied"), "success"), () => toast(t("admin.labelers.copyFailed"), "error"))}>{t("admin.common.copy")}</Btn>
      </div>
    </div>
  );
}

/** Creates a system labeler; the generated credentials are shown once and dropped on close. */
export function CreateLabelerDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const t = useT();
  const [name, setName] = useState("");
  const [created, setCreated] = useState<LabelerCreated | null>(null);
  const create = useUserAct((n: string) => labelers.create(n.trim()), [["admin-users"]]);
  const close = () => { setName(""); setCreated(null); onClose(); };
  return (
    <Dialog open={open} onClose={close} dismissable={!created && !create.isPending} title={created ? t("admin.labelers.created") : t("admin.labelers.createSystem")}
      footer={created ? <Btn variant="primary" onClick={close}>{t("admin.labelers.iSavedTheCredentials")}</Btn> : <><Btn onClick={close}>{t("admin.common.cancel")}</Btn><Btn variant="primary" disabled={create.isPending} onClick={() => create.mutate(name, { onSuccess: setCreated })}>{t("admin.common.create")}</Btn></>}>
      {created ? (
        <div className="space-y-3">
          <p role="alert" className="rounded-xl border border-gold bg-yellow-50 px-3 py-2 text-xs font-bold text-gold-deep">{t("admin.labelers.thePasswordIsShown")}</p>
          <Secret label={t("admin.labelers.login")} value={created.login} />
          <Secret label={t("admin.common.password")} value={created.password} />
        </div>
      ) : (
        <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); if (!create.isPending) create.mutate(name, { onSuccess: setCreated }); }}>
          <Field label={t("admin.common.displayName")} hint={t("admin.labelers.optionalLoginAndPassword")}><Input value={name} onChange={(e) => setName(e.target.value)} /></Field>
        </form>
      )}
    </Dialog>
  );
}
