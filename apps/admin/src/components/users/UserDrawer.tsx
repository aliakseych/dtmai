"use client";
import { useEnum, useT } from "@/lib/i18n";
import { useConfirm } from "@/components/ui/confirm";
import { useAuth } from "@/lib/auth";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { UserStatsPanel } from "@/components/stats";
import { Badge, Btn, Check, ErrorBox, Field, Input, Spinner } from "@/components/ui/controls";
import { Drawer } from "@/components/ui/overlay";
import { useSubjects } from "@/lib/catalog";
import { ALL_ROLES, users, useUserAct, type AdminUser } from "@/lib/users";
import { nm } from "@/lib/util";
import { useToast } from "@dtmai/ui";

function Stats({ id }: { id: string }) {
  const stats = useQuery({ queryKey: ["admin-user-stats", id], queryFn: () => users.stats(id) });
  const subjects = useSubjects();
  const subjectName = (sid: string) => nm(subjects.data?.find((s) => s.id === sid)?.names, sid.slice(0, 8));
  if (stats.isLoading) return <div className="grid place-items-center p-6"><Spinner /></div>;
  if (stats.error) return <ErrorBox error={stats.error} />;
  return stats.data ? <UserStatsPanel stats={stats.data} subjectName={subjectName} /> : null;
}

/** Detail drawer: edit display name / roles / status, reset password, and view learner statistics. */
export function UserDrawer({ user: row, onClose, canEdit }: { user: AdminUser | null; onClose: () => void; canEdit: boolean }) {
  const t = useT();
  const { me } = useAuth();
  const en = useEnum();
  const [ask, confirmNode] = useConfirm();
  const fresh = useQuery({ queryKey: ["admin-user", row?.id], queryFn: () => users.get(row!.id), enabled: !!row });
  const user = fresh.data && fresh.data.id === row?.id ? fresh.data : row;
  const toast = useToast();
  const [name, setName] = useState("");
  const [roles, setRoles] = useState<string[]>([]);
  const [pw, setPw] = useState("");
  const rolesKey = user?.roles.join(",");
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { setName(user?.display_name ?? ""); setRoles(user?.roles ?? []); setPw(""); }, [user?.id, user?.display_name, rolesKey]);
  const keys = [["admin-users"], ["admin-user"]] as const;
  const save = useUserAct((a: { id: string; name: string; roles: string[] }) => users.patch(a.id, { display_name: a.name, roles: a.roles }), keys, "admin.users.saved");
  const toggle = useUserAct((a: { id: string; disable: boolean }) => users.patch(a.id, { status: a.disable ? "disabled" : "active" }), keys, "admin.users.statusChanged");
  const reset = useUserAct((a: { id: string; password: string }) => users.resetPassword(a.id, a.password), [], "admin.users.passwordReset");
  const dirty = !!user && (name !== (user.display_name ?? "") || [...roles].sort().join() !== [...user.roles].sort().join());
  const disabled = user?.status === "disabled";
  const isSelf = !!user && user.id === me?.id;
  const rolesChanged = !!user && [...roles].sort().join() !== [...user.roles].sort().join();
  const selfDemote = isSelf && !!user?.roles.includes("admin") && !roles.includes("admin");
  const label = user ? (user.display_name || user.email || user.id.slice(0, 8)) : "";
  return (
    <Drawer open={!!user} onClose={onClose} width="max-w-2xl" title={user ? (user.display_name || user.email || "User") : ""}
      footer={canEdit && user && <Btn variant="primary" disabled={!dirty || !name.trim() || roles.length === 0 || save.isPending || selfDemote} onClick={() => { const go = () => save.mutate({ id: user.id, name: name.trim(), roles }, { onSuccess: onClose }); if (rolesChanged) ask({ title: t("admin.users.confirmRoles"), name: label, body: roles.join(", "), confirmLabel: t("admin.users.saveChanges") }, go); else go(); }}>{t("admin.users.saveChanges")}</Btn>}>
      {user && <div className="space-y-5">
        <section className="space-y-3">
          <div className="flex flex-wrap items-center gap-2 text-xs text-ink-soft">
            <Badge tone={disabled ? "red" : "green"}>{en("userStatus", user.status)}</Badge>
            {user.is_system && <Badge tone="blue">{t("admin.common.system")}</Badge>}
            <span>{user.email ?? (user.telegram_username ? `@${user.telegram_username}` : "")}</span>
            <span>{t("admin.users.id")} <code className="select-all">{user.id}</code></span>
            <Btn variant="ghost" onClick={() => navigator.clipboard.writeText(user.id).then(() => toast(t("admin.common.copied"), "success"))}>{t("admin.common.copy")}</Btn>
          </div>
          <Field label={t("admin.common.displayName")}><Input value={name} disabled={!canEdit} onChange={(e) => setName(e.target.value)} /></Field>
          <fieldset className="flex flex-wrap gap-x-4 gap-y-1">
            <legend className="mb-0.5 text-xs font-extrabold uppercase tracking-wide text-ink-soft">{t("admin.users.roles")}</legend>
            {ALL_ROLES.map((r) => <Check key={r} label={en("role", r)} checked={roles.includes(r)} onChange={(on) => canEdit && setRoles((x) => (on ? [...x, r] : x.filter((y) => y !== r)))} />)}
          </fieldset>
          {canEdit && <div className="flex flex-wrap items-end gap-2 border-t border-line pt-3">
            <Btn variant={disabled ? "default" : "danger"} disabled={toggle.isPending || (isSelf && !disabled)} onClick={() => ask({ title: disabled ? t("admin.users.enableAccount") : t("admin.users.disableAccount"), name: label, danger: !disabled, confirmLabel: disabled ? t("admin.users.enableAccount") : t("admin.users.disableAccount") }, () => toggle.mutate({ id: user.id, disable: !disabled }))}>{disabled ? t("admin.users.enableAccount") : t("admin.users.disableAccount")}</Btn>
            {isSelf && !disabled && <p className="basis-full text-xs text-ink-soft">{t("admin.users.selfProtect")}</p>}
            <Field label={t("admin.users.newPassword")} className="ml-auto"><Input type="password" autoComplete="new-password" value={pw} onChange={(e) => setPw(e.target.value)} placeholder={t("admin.users.min8Characters")} /></Field>
            <Btn disabled={pw.length < 8 || reset.isPending} onClick={() => reset.mutate({ id: user.id, password: pw }, { onSuccess: () => setPw("") })}>{t("admin.users.resetPassword")}</Btn>
          </div>}
        </section>
        <Stats id={user.id} />
      </div>}
      {confirmNode}
    </Drawer>
  );
}
