"use client";
import Link from "next/link";
import { useLocale, useT } from "@dtmai/i18n";
import { DREAM_PLACEHOLDER } from "@/components/lyceums/LyceumMedia";
import { latestCompetition, useLyceumDetail } from "@/components/lyceums/useLyceumDetail";
import { LyceumName } from "@/components/lyceums/LyceumName";
import { useAuth } from "@/lib/auth";
import { dreamIds } from "@/lib/dreams";
import { mediaUrl } from "@/lib/env";
import { pick } from "@/lib/localized";

/** Learn-home banner: "Future <lyceum> student" with campus photo, logo and last competition ratio. */
export function DreamPin() {
  const t = useT();
  const { locale } = useLocale();
  const { me } = useAuth();
  const ids = dreamIds(me);
  const { data } = useLyceumDetail(ids[0]);
  if (!data) return null;
  const photo = data.profile.campus_photo_url;
  const ratio = latestCompetition(data);
  const rest = ids.slice(1);
  return (
    <div className="flex flex-col gap-2">
    <section className="relative isolate flex min-h-32 items-end overflow-hidden rounded-card border-2 border-line bg-brand-soft">
      {photo && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={mediaUrl(photo)} alt="" className="absolute inset-0 -z-10 h-full w-full object-cover" />
      )}
      {photo && <div className="absolute inset-0 -z-10 bg-gradient-to-t from-black/75 via-black/30 to-transparent" aria-hidden="true" />}
      <div className="flex w-full items-center gap-3 p-4">
        {data.profile.logo_url && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={mediaUrl(data.profile.logo_url)} alt="" className="h-12 w-12 shrink-0 rounded-xl border-2 border-line bg-white object-contain p-1" />
        )}
        <div className="min-w-0 flex-1">
          <p className={`break-words font-extrabold ${photo ? "text-white" : "text-ink"}`}>
            {t("dream.pin.title", { name: pick(data.names, locale) })}
          </p>
          {ratio != null && (
            <p className={`text-sm font-bold ${photo ? "text-white/90" : "text-ink-soft"}`}>
              {t("dream.pin.competition", { ratio: ratio.toFixed(1) })}
            </p>
          )}
        </div>
        {!photo && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={DREAM_PLACEHOLDER} alt="" className="hidden h-24 w-32 shrink-0 object-contain sm:block" />
        )}
        <Link href="/lyceums/" className="shrink-0 rounded-xl bg-white px-3 py-2 text-sm font-extrabold text-brand">
          {t("dream.pin.change")}
        </Link>
      </div>
    </section>
      {rest.length > 0 && (
        <ol start={2} className="flex flex-wrap gap-2">
          {rest.map((id, i) => (
            <li key={id} className="rounded-full border-2 border-line bg-white px-3 py-1 text-sm font-bold text-ink">
              {i + 2}. <LyceumName id={id} />
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
