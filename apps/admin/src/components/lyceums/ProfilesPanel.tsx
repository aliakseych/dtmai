"use client";
import { useT } from "@/lib/i18n";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { lyceums, type LyceumRow } from "@/lib/lyceums";
import { nm } from "@/lib/util";
import { Btn, Input, Toolbar } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";
import { ProfileEditor } from "./ProfileEditor";

export function ProfilesPanel() {
  const t = useT();
  const [q, setQ] = useState("");
  const [edit, setEdit] = useState<LyceumRow | null>(null);
  const list = useQuery({ queryKey: ["lyceum-list", q], queryFn: () => lyceums.list(q) });
  return (
    <>
      <Toolbar><Input className="max-w-xs" type="search" placeholder={t("admin.lyceums.searchLyceums")} value={q} onChange={(e) => setQ(e.target.value)} /></Toolbar>
      <div className="min-h-0 flex-1 overflow-auto">
        <DataTable rows={list.data} loading={list.isLoading} error={list.error} rowKey={(r) => r.id} empty={t("admin.lyceums.noLyceumsFound")} onRow={setEdit}
          cols={[
            { key: "n", head: t("admin.lyceums.lyceum"), cell: (r) => nm(r.names) },
            { key: "c", head: t("admin.common.code"), cell: (r) => r.code },
            { key: "y", head: t("admin.lyceums.latestYear"), cell: (r) => r.latest_year ?? "—" },
            { key: "q", head: t("admin.lyceums.quota"), cell: (r) => r.quota ?? "—" },
            { key: "a", head: "", cell: (r) => <Btn onClick={() => setEdit(r)}>{t("admin.lyceums.editProfile")}</Btn> },
          ]} />
      </div>
      <ProfileEditor lyceum={edit} onClose={() => setEdit(null)} />
    </>
  );
}
