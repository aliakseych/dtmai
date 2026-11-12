"use client";
import { useLocale, useT } from "@dtmai/i18n";
import { mediaUrl } from "@/lib/env";
import { pick } from "@/lib/localized";
import type { LyceumDetailData } from "./useLyceumDetail";

type Profile = LyceumDetailData["profile"];

const isHttp = (u: string) => /^https?:\/\//i.test(u);

/** Campus map (embed, coordinates link, or image), floor plans, specializations and special offerings. Every block renders only when present. */
export function CampusSections({ profile: p }: { profile: Profile }) {
  const t = useT();
  const { locale } = useLocale();
  const map = p.map;
  const hasCoords = map?.lat != null && map?.lng != null;
  const hasMap = !!map && (hasCoords || !!map.embed_url || !!map.image_url);
  const mapsHref = hasCoords ? `https://www.google.com/maps?q=${map!.lat},${map!.lng}` : null;
  return (
    <>
      {hasMap && (
        <section aria-label={t("lyceums.map")}>
          <h3 className="mb-2 text-lg font-extrabold text-ink">{t("lyceums.map")}</h3>
          {map!.embed_url && isHttp(map!.embed_url) && (
            <iframe
              src={map!.embed_url}
              title={t("lyceums.map")}
              loading="lazy"
              referrerPolicy="no-referrer"
              className="h-64 w-full rounded-2xl border-2 border-line"
            />
          )}
          {!map!.embed_url && map!.image_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={mediaUrl(map!.image_url)} alt={t("lyceums.map")} loading="lazy" className="w-full rounded-2xl border-2 border-line object-cover" />
          )}
          {mapsHref && (
            <a href={mapsHref} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-11 items-center font-bold text-brand underline">
              {t("lyceums.openMap")}
            </a>
          )}
        </section>
      )}

      {p.buildings.some((b) => (b.floor_plans ?? []).length > 0) && (
        <section aria-label={t("lyceums.buildings")}>
          <h3 className="mb-2 text-lg font-extrabold text-ink">{t("lyceums.buildings")}</h3>
          <ul className="flex flex-col gap-4">
            {p.buildings
              .filter((b) => (b.floor_plans ?? []).length > 0)
              .map((b, i) => (
                <li key={i}>
                  <p className="mb-2 font-bold text-ink">{pick(b.name, locale)}</p>
                  <ul className="flex max-w-full snap-x gap-2 overflow-x-auto pb-2">
                    {(b.floor_plans ?? []).map((fp) => (
                      <li key={fp.image_url} className="w-64 shrink-0 snap-start sm:w-80">
                        <a href={mediaUrl(fp.image_url)} target="_blank" rel="noopener noreferrer" className="block overflow-hidden rounded-2xl border-2 border-line bg-white">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img src={mediaUrl(fp.image_url)} alt={pick(fp.label, locale) || t("lyceums.floorPlan")} loading="lazy" className="h-44 w-full object-contain sm:h-56" />
                        </a>
                        {pick(fp.label, locale) && <p className="mt-1 text-sm text-ink-soft">{pick(fp.label, locale)}</p>}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
          </ul>
        </section>
      )}

      {p.specializations.length > 0 && (
        <section aria-label={t("lyceums.specializations")}>
          <h3 className="mb-2 text-lg font-extrabold text-ink">{t("lyceums.specializations")}</h3>
          <ul className="flex flex-col gap-3">
            {p.specializations.map((s, i) => (
              <li key={i} className="rounded-2xl border-2 border-line p-3">
                <p className="text-sm font-bold text-ink-soft">{s.field_code}</p>
                <p className="break-words text-lg font-extrabold text-ink">{pick(s.name, locale)}</p>
                {pick(s.description, locale) && <p className="mt-1 whitespace-pre-line break-words text-ink">{pick(s.description, locale)}</p>}
                {(s.second_year_subjects ?? []).length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm font-bold text-ink-soft">{t("lyceums.secondYearSubjects")}</p>
                    <ul className="mt-1 flex flex-wrap gap-2">
                      {(s.second_year_subjects ?? []).map((x, j) => (
                        <li key={j} className="rounded-full border-2 border-line px-3 py-1 text-sm font-bold text-ink">
                          {pick(x, locale)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {p.offerings.length > 0 && (
        <section aria-label={t("lyceums.offerings")}>
          <h3 className="mb-2 text-lg font-extrabold text-ink">{t("lyceums.offerings")}</h3>
          <ul className="flex flex-col gap-3">
            {p.offerings.map((o, i) => (
              <li key={i} className="rounded-2xl border-2 border-line p-3">
                <p className="break-words font-extrabold text-ink">{pick(o.title, locale)}</p>
                {pick(o.description, locale) && <p className="mt-1 whitespace-pre-line break-words text-ink">{pick(o.description, locale)}</p>}
                {pick(o.taught_by, locale) && (
                  <p className="mt-1 text-sm text-ink-soft">{t("lyceums.taughtBy", { who: pick(o.taught_by, locale) })}</p>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
