"use client";
import { useT } from "@/lib/i18n";
import { useState } from "react";
import { ActivityPanel } from "@/components/labelers/ActivityPanel";
import { CreateLabelerDialog } from "@/components/labelers/CreateLabelerDialog";
import { LeaderboardPanel } from "@/components/labelers/LeaderboardPanel";
import { Btn, PageHeader, Tabs } from "@/components/ui/controls";
import { UserDrawer } from "@/components/users/UserDrawer";
import { UsersTable } from "@/components/users/UsersTable";
import { useAuth } from "@/lib/auth";
import type { AdminUser } from "@/lib/users";

type Tab = "list" | "activity" | "leaderboard";

export default function LabelersPage() {
  const t = useT();
  const { isAdmin } = useAuth();
  const [tab, setTab] = useState<Tab>("list");
  const [sel, setSel] = useState<AdminUser | null>(null);
  const [creating, setCreating] = useState(false);
  return (
    <>
      <PageHeader title={t("admin.labelers.labelers")} sub={t("admin.labelers.systemAndHumanLabelers")}
        actions={isAdmin && <Btn variant="primary" onClick={() => setCreating(true)}>{t("admin.labelers.createSystemLabeler")}</Btn>} />
      <Tabs value={tab} onChange={setTab} items={[{ id: "list", label: t("admin.labelers.labelers") }, { id: "activity", label: t("admin.labelers.activityLog") }, { id: "leaderboard", label: t("admin.labelers.leaderboard") }]} />
      {tab === "list" && <UsersTable queryKey="labelers" roles={["labeler"]} role="labeler" allowAnyRole={false} onOpen={setSel} selected={sel?.id} />}
      {tab === "activity" && <ActivityPanel />}
      {tab === "leaderboard" && <LeaderboardPanel />}
      <CreateLabelerDialog open={creating} onClose={() => setCreating(false)} />
      <UserDrawer user={sel} onClose={() => setSel(null)} canEdit={isAdmin} />
    </>
  );
}
