"use client";
import { useState } from "react";
import { PageHeader, Tabs } from "@/components/ui/controls";
import { AdmissionPanel } from "@/components/lyceums/AdmissionPanel";
import { ImportPanel } from "@/components/lyceums/ImportPanel";
import { PostModeration } from "@/components/lyceums/PostModeration";
import { ProfilesPanel } from "@/components/lyceums/ProfilesPanel";
import { RepApplications } from "@/components/lyceums/RepApplications";

type Tab = "profiles" | "reps" | "posts" | "import" | "admission";

export default function LyceumsPage() {
  const [tab, setTab] = useState<Tab>("profiles");
  return (
    <>
      <PageHeader title="Lyceums" sub="Profiles, representative applications, post moderation and per-year stats import." />
      <Tabs value={tab} onChange={setTab} items={[
        { id: "profiles", label: "Profiles" },
        { id: "reps", label: "Rep applications" },
        { id: "posts", label: "Post moderation" },
        { id: "import", label: "Stats import" },
        { id: "admission", label: "Admission plan" },
      ]} />
      {tab === "profiles" && <ProfilesPanel />}
      {tab === "reps" && <RepApplications />}
      {tab === "posts" && <PostModeration />}
      {tab === "import" && <ImportPanel />}
      {tab === "admission" && <AdmissionPanel />}
    </>
  );
}
