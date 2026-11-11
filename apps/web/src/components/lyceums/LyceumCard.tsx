"use client";
import { useT } from "@dtmai/i18n";
import { Card } from "@dtmai/ui";
import { LyceumDetailView, LyceumHeading } from "./LyceumDetailView";
import { LyceumCover } from "./LyceumMedia";
import { academicYear } from "./StatsTable";
import { useLyceumDetail, type LyceumDetailData } from "./useLyceumDetail";

type Summary = { id: string; competition_ratio: number | null; latest_year: number | null };

function Expanded({ id }: { id: string }) {
  const t = useT();
  const { data, reload } = useLyceumDetail(id);
  if (data === undefined) return <p className="py-4 text-center text-ink-soft">{t("common.loading")}</p>;
  if (data === null) return <p role="alert" className="py-4 text-center text-ink-soft">{t("common.error")}</p>;
  return <LyceumDetailView detail={data} onDreamChanged={reload} />;
}

export function LyceumCard({
  summary,
  detail,
  title,
  open,
  onToggle,
}: {
  summary: Summary;
  detail: LyceumDetailData | undefined;
  title: string;
  open: boolean;
  onToggle: () => void;
}) {
  const t = useT();
  const p = detail?.profile;
  return (
    <Card className="p-3 sm:p-4">
      <button type="button" aria-expanded={open} onClick={onToggle} className="block w-full text-left">
        <div className="pb-5">
          <LyceumCover photo={p?.campus_photo_url} logo={p?.logo_url} className="h-28 sm:h-36" />
        </div>
        {detail ? <LyceumHeading d={detail} /> : <h2 className="break-words text-lg text-ink">{title}</h2>}
        <p className="mt-1 text-ink-soft">
          {summary.competition_ratio != null ? `${t("lyceums.competition")}: ${summary.competition_ratio.toFixed(1)}` : "—"}
          {summary.latest_year ? ` · ${t("lyceums.lastData", { year: academicYear(summary.latest_year) })}` : ""}
          {detail ? ` · ${t("lyceums.dreamers", { count: detail.dreamers_count })}` : ""}
        </p>
      </button>
      {open && (
        <div className="mt-4 border-t-2 border-line pt-4">
          <Expanded id={summary.id} />
        </div>
      )}
    </Card>
  );
}
