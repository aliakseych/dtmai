"use client";
import { useState } from "react";
import { Card } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { PageTitle } from "@/components/PageTitle";
import { api } from "@/lib/api";
import { fmt, pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";

const DASH = "—";

function Stats({ lyceumId }: { lyceumId: string }) {
  const t = useT();
  const { locale } = useLocale();
  const ratio = new Intl.NumberFormat(fmt(locale).resolvedOptions().locale, { maximumFractionDigits: 1, minimumFractionDigits: 1 });
  const detail = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums/{lyceum_id}", { params: { path: { lyceum_id: lyceumId } } })), [lyceumId]);
  const langs = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums/languages")), []);
  const langName = (id: string) => {
    const l = langs.state.status === "ready" ? langs.state.data.find((x) => x.id === id) : undefined;
    return l ? pick(l.names, locale) : "";
  };
  return (
    <AsyncView state={detail.state} onRetry={detail.reload} isEmpty={(d) => d.stats.length === 0} emptyText={t("lyceums.empty")}>
      {(d) => (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[34rem] text-left">
            <thead className="text-sm uppercase text-ink-soft">
              <tr>
                <th scope="col" className="py-2">{t("lyceums.year")}</th>
                <th scope="col">{t("lyceums.speciality")}</th>
                <th scope="col">{t("lyceums.quota")}</th>
                <th scope="col">{t("lyceums.applications")}</th>
                <th scope="col">{t("lyceums.competition")}</th>
                <th scope="col">{t("lyceums.passing")}</th>
              </tr>
            </thead>
            <tbody>
              {d.stats.map((r) => (
                <tr key={r.id} className="border-t-2 border-line">
                  <td className="py-2">{r.year}</td>
                  <td>
                    {r.name} <span className="text-ink-soft">({langName(r.language_id) || r.speciality_code})</span>
                  </td>
                  <td>{r.quota}</td>
                  <td>{r.applications}</td>
                  <td>{r.competition_ratio != null ? ratio.format(r.competition_ratio) : DASH}</td>
                  <td>{r.passing_score != null ? r.passing_score : DASH}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AsyncView>
  );
}

export function LyceumsView() {
  const t = useT();
  const { locale } = useLocale();
  const [q, setQ] = useState("");
  const [open, setOpen] = useState<string | null>(null);
  const { state, reload } = useAsync(() => api.unwrap(api.client.GET("/v1/lyceums", { params: { query: { q: q || undefined } } })), [q]);
  return (
    <>
      <PageTitle>{t("lyceums.title")}</PageTitle>
      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder={t("lyceums.search")}
        aria-label={t("lyceums.search")}
        className="mb-4 w-full rounded-2xl border-2 border-line bg-snow px-4 py-3 text-ink focus:border-blue focus:bg-white"
      />
      <AsyncView state={state} onRetry={reload} isEmpty={(d) => d.length === 0} emptyText={t("lyceums.none")}>
        {(list) => (
          <div className="flex flex-col gap-3">
            {list.map((l) => (
              <Card key={l.id}>
                <button type="button" aria-expanded={open === l.id} onClick={() => setOpen(open === l.id ? null : l.id)} className="w-full text-left">
                  <h2 className="text-lg text-ink">{pick(l.names, locale)}</h2>
                  <p className="text-ink-soft">
                    {l.competition_ratio != null ? `${t("lyceums.competition")}: ${l.competition_ratio.toFixed(1)}` : DASH}
                    {l.latest_year ? ` · ${l.latest_year}` : ""}
                  </p>
                </button>
                {open === l.id && (
                  <div className="mt-3">
                    <Stats lyceumId={l.id} />
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </AsyncView>
    </>
  );
}
