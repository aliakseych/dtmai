"use client";
import { useT } from "@dtmai/i18n";
import { Card } from "@dtmai/ui";
import { DormitoryBadge } from "./DormitoryBadge";
import { LyceumDetailView } from "./LyceumDetailView";
import { LyceumCover } from "./LyceumMedia";
import { academicYear } from "./StatsTable";
import type { LyceumRow } from "@/lib/api";
import { useLyceumDetail } from "./useLyceumDetail";

/** Fetches the full profile only when the card is expanded. */
function Expanded({ id }: { id: string }) {
  const t = useT();
  const { data, reload } = useLyceumDetail(id);
  if (data === undefined) return <p className="py-4 text-center text-ink-soft">{t("common.loading")}</p>;
  if (data === null) return <p role="alert" className="py-4 text-center text-ink-soft">{t("common.error")}</p>;
  return <LyceumDetailView detail={data} onDreamChanged={reload} />;
}

export function LyceumCard({ summary, title, cityName, open, onToggle }: { summary: LyceumRow; title: string; cityName?: string; open: boolean; onToggle: () => void }) {
  const t = useT();
  const ratio = summary.competition;
  const year = summary.competition_year;
  return (
    <Card pad="none" className="p-3 sm:p-4">
      <button type="button" aria-expanded={open} onClick={onToggle} className="block w-full text-left">
        <div className="pb-5">
          <LyceumCover photo={summary.campus_photo_url} logo={summary.logo_url} className="h-28 sm:h-36" />
        </div>
        <h2 className="break-words text-lg text-ink">{title}</h2>
        {cityName && <p className="break-words text-sm text-ink-soft">{cityName}</p>}
        <p className="mt-1 text-ink-soft">
          <span className="font-extrabold text-brand">
            {ratio != null ? `${t("lyceums.competition")}: ${ratio.toFixed(1)}` : "—"}
          </span>
          {year ? ` · ${t("lyceums.lastData", { year: academicYear(year) })}` : ""}
        </p>
        {(summary.seats_total != null || summary.admission_ratio != null) && (
          <p className="mt-1 text-sm text-ink-soft">
            {summary.seats_total != null && t("lyceums.admission.seatsTotal", { count: summary.seats_total })}
            {summary.seats_total != null && summary.admission_ratio != null && " · "}
            {summary.admission_ratio != null && `${t("lyceums.admission.ratio")}: ${summary.admission_ratio.toFixed(1)}`}
          </p>
        )}
        <DormitoryBadge status={summary.dormitory_status} className="mt-2" />
      </button>
      {summary.contact && (summary.contact.phones.length > 0 || summary.contact.telegram) && (
        <p className="mt-2 flex flex-wrap gap-3 text-sm">
          {summary.contact.phones[0] && (
            <a href={`tel:${summary.contact.phones[0]}`} className="font-bold text-brand">
              {summary.contact.phones[0]}
            </a>
          )}
          {summary.contact.telegram && (
            <a href={summary.contact.telegram} target="_blank" rel="noopener noreferrer" className="font-bold text-brand">
              {t("lyceums.admission.telegram")}
            </a>
          )}
        </p>
      )}
      {open && (
        <div className="mt-4 border-t-2 border-line pt-4">
          <Expanded id={summary.id} />
        </div>
      )}
    </Card>
  );
}
