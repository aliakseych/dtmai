"use client";
import { useT } from "@/lib/i18n";
import { useState } from "react";
import { PageHeader, Tabs } from "@/components/ui/controls";
import { AdmissionPanel } from "@/components/lyceums/AdmissionPanel";
import { ImportPanel } from "@/components/lyceums/ImportPanel";
import { PostModeration } from "@/components/lyceums/PostModeration";
import { ProfilesPanel } from "@/components/lyceums/ProfilesPanel";
import { RepApplications } from "@/components/lyceums/RepApplications";

type Tab = "profiles" | "reps" | "posts" | "import" | "admission";

export default function LyceumsPage() {
  const t = useT();
  const [tab, setTab] = useState<Tab>("profiles");
  return (
    <>
      <PageHeader title={t("admin.lyceums.lyceums")} sub={t("admin.lyceums.profilesRepresentativeApplicationsPost")} />
      <Tabs value={tab} onChange={setTab} items={[
        { id: "profiles", label: t("admin.lyceums.profiles") },
        { id: "reps", label: t("admin.lyceums.repApplications") },
        { id: "posts", label: t("admin.lyceums.postModeration") },
        { id: "import", label: t("admin.lyceums.statsImport") },
        { id: "admission", label: t("admin.lyceums.admissionPlan") },
      ]} />
      {tab === "profiles" && <ProfilesPanel />}
      {tab === "reps" && <RepApplications />}
      {tab === "posts" && <PostModeration />}
      {tab === "import" && <ImportPanel />}
      {tab === "admission" && <AdmissionPanel />}
    </>
  );
}
