"use client";
import { useT } from "@/lib/i18n";
import { useState } from "react";
import { Btn, Check, Field, Input } from "@/components/ui/controls";
import { Dialog } from "@/components/ui/overlay";
import { STAFF_ROLES, users, useUserAct } from "@/lib/users";

const EMPTY = { email: "", display_name: "", password: "", roles: ["editor"] as string[] };

export function CreateStaffDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const t = useT();
  const [f, setF] = useState(EMPTY);
  const create = useUserAct(users.create, [["admin-users"]], "admin.users.staffCreated");
  const valid = f.email.includes("@") && f.display_name.trim() !== "" && f.password.length >= 8 && f.roles.length > 0;
  const close = () => { setF(EMPTY); onClose(); };
  return (
    <Dialog open={open} onClose={close} title={t("admin.common.createStaffAccount")}
      footer={<><Btn onClick={close}>{t("admin.common.cancel")}</Btn><Btn variant="primary" disabled={!valid || create.isPending} onClick={() => create.mutate({ ...f, display_name: f.display_name.trim() }, { onSuccess: close })}>{t("admin.common.create")}</Btn></>}>
      <form className="space-y-3" onSubmit={(e) => e.preventDefault()}>
        <Field label={t("admin.common.email")}><Input type="email" autoComplete="off" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></Field>
        <Field label={t("admin.common.displayName")}><Input value={f.display_name} onChange={(e) => setF({ ...f, display_name: e.target.value })} /></Field>
        <Field label={t("admin.common.password")} hint={t("admin.users.atLeast8Characters")}><Input type="text" autoComplete="off" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} /></Field>
        <fieldset className="flex flex-wrap gap-x-4 gap-y-1">
          <legend className="mb-0.5 text-[11px] font-extrabold uppercase tracking-wide text-ink-soft">{t("admin.users.roles")}</legend>
          {STAFF_ROLES.map((r) => <Check key={r} label={r} checked={f.roles.includes(r)} onChange={(on) => setF({ ...f, roles: on ? [...f.roles, r] : f.roles.filter((x) => x !== r) })} />)}
        </fieldset>
      </form>
    </Dialog>
  );
}
