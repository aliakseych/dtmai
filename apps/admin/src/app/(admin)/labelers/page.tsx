"use client";
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
  const { isAdmin } = useAuth();
  const [tab, setTab] = useState<Tab>("list");
  const [sel, setSel] = useState<AdminUser | null>(null);
  const [creating, setCreating] = useState(false);
  return (
    <>
      <PageHeader title="Labelers" sub="System and human labelers, their activity log and productivity."
        actions={isAdmin && <Btn variant="primary" onClick={() => setCreating(true)}>Create system labeler</Btn>} />
      <Tabs value={tab} onChange={setTab} items={[{ id: "list", label: "Labelers" }, { id: "activity", label: "Activity log" }, { id: "leaderboard", label: "Leaderboard" }]} />
      {tab === "list" && <UsersTable queryKey="labelers" roles={["labeler"]} role="labeler" allowAnyRole={false} onOpen={setSel} selected={sel?.id} />}
      {tab === "activity" && <ActivityPanel />}
      {tab === "leaderboard" && <LeaderboardPanel />}
      <CreateLabelerDialog open={creating} onClose={() => setCreating(false)} />
      <UserDrawer user={sel} onClose={() => setSel(null)} canEdit={isAdmin} />
    </>
  );
}
