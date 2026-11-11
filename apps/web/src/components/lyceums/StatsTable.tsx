"use client";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { api } from "@/lib/api";
import { fmt, pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";
import type { LyceumDetailData } from "./useLyceumDetail";

const DASH = "—";
/** Admission campaign label: stats year 2026 → "2026-2027". */
export const academicYear = (y: number) => `${y}-${y + 1}`;

export function StatsTable({ detail: d }: { detail: LyceumDetailData }) {
  const t = useT();
  const { locale } = useLocale();
  const ratio = new Intl.NumberFormat(fmt(locale).resolvedOptions().locale, { maximumFractionDigits: 1, minimumFractionDigits: 1 });
  const langs = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums/languages")), []);
  const langName = (id: string) => {
    const l = langs.state.status === "ready" ? langs.state.data.find((x) => x.id === id) : undefined;
    return l ? pick(l.names, locale) : "";
  };
  if (d.stats.length === 0) return <p className="py-4 text-center text-ink-soft">{t("lyceums.empty")}</p>;
  return (
    <>
      {/* Mobile: one card per row; desktop: fixed-layout table. */}
      <ul className="flex flex-col gap-3 md:hidden">
        {d.stats.map((r) => (
          <li key={r.id} className="rounded-2xl border-2 border-line p-3">
            <p className="text-sm font-bold text-ink-soft">{academicYear(r.year)}</p>
            <p className="break-words font-bold text-ink">
              {r.name} <span className="font-normal text-ink-soft">({langName(r.language_id) || r.speciality_code})</span>
            </p>
            <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-sm">
              <dt className="text-ink-soft">{t("lyceums.quota")}</dt>
              <dd className="text-right">{r.quota}</dd>
              <dt className="text-ink-soft">{t("lyceums.applications")}</dt>
              <dd className="text-right">{r.applications}</dd>
              <dt className="text-ink-soft">{t("lyceums.competition")}</dt>
              <dd className="text-right">{r.competition_ratio != null ? ratio.format(r.competition_ratio) : DASH}</dd>
              <dt className="text-ink-soft">{t("lyceums.passing")}</dt>
              <dd className="text-right">{r.passing_score != null ? r.passing_score : DASH}</dd>
            </dl>
          </li>
        ))}
      </ul>
      <table className="hidden w-full table-fixed text-left md:table">
        <colgroup>
          <col className="w-[14%]" />
          <col className="w-[32%]" />
          <col className="w-[10%]" />
          <col className="w-[14%]" />
          <col className="w-[15%]" />
          <col className="w-[15%]" />
        </colgroup>
        <thead className="text-xs uppercase text-ink-soft">
          <tr>
            <th scope="col" className="px-2 py-2 align-bottom">{t("lyceums.year")}</th>
            <th scope="col" className="px-2 py-2 align-bottom">{t("lyceums.speciality")}</th>
            <th scope="col" className="px-2 py-2 align-bottom">{t("lyceums.quota")}</th>
            <th scope="col" className="px-2 py-2 align-bottom">{t("lyceums.applications")}</th>
            <th scope="col" className="px-2 py-2 align-bottom">{t("lyceums.competition")}</th>
            <th scope="col" className="px-2 py-2 align-bottom">{t("lyceums.passing")}</th>
          </tr>
        </thead>
        <tbody>
          {d.stats.map((r) => (
            <tr key={r.id} className="border-t-2 border-line align-top">
              <td className="px-2 py-2">{academicYear(r.year)}</td>
              <td className="break-words px-2 py-2">
                {r.name} <span className="text-ink-soft">({langName(r.language_id) || r.speciality_code})</span>
              </td>
              <td className="px-2 py-2">{r.quota}</td>
              <td className="px-2 py-2">{r.applications}</td>
              <td className="px-2 py-2">{r.competition_ratio != null ? ratio.format(r.competition_ratio) : DASH}</td>
              <td className="px-2 py-2">{r.passing_score != null ? r.passing_score : DASH}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
