"use client";
import Link from "next/link";
import { useLocale, useT } from "@dtmai/i18n";
import { mediaUrl } from "@/lib/env";
import { pick } from "@/lib/localized";
import { AdmissionSeats } from "./AdmissionSeats";
import { DreamButton } from "./DreamButton";
import { LyceumCover } from "./LyceumMedia";
import { PostsByKind } from "./PostsByKind";
import { StatsTable } from "./StatsTable";
import { VerifiedBadge } from "./VerifiedBadge";
import type { Names } from "@/lib/api";
import { DormitoryBadge } from "./DormitoryBadge";
import type { LyceumDetailData } from "./useLyceumDetail";

const safeHttp = (u: string) => (/^https?:\/\//i.test(u) ? u : `https://${u}`);

export function LyceumDetailView({ detail: d, onDreamChanged }: { detail: LyceumDetailData; onDreamChanged: () => void }) {
  const t = useT();
  const { locale } = useLocale();
  const p = d.profile;
  const description = pick(p.description, locale);
  const dorm = d.profile;
  const dormDescription = pick(dorm.dormitory_description as Names | undefined, locale);
  const c = p.contacts;
  const tg = c.telegram ? (c.telegram.startsWith("http") ? c.telegram : `https://t.me/${c.telegram.replace(/^@/, "")}`) : null;
  const hasContacts = !!(c.phone || c.telegram || c.email || p.website);
  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-3 pb-5">
        <LyceumCover photo={p.campus_photo_url} logo={p.logo_url} className="h-40 sm:h-56" />
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          {p.verified_rep && <VerifiedBadge />}
          <p className="font-bold text-ink-soft">
            {[p.university_name, t("lyceums.dreamers", { count: d.dreamers_count })].filter(Boolean).join(" · ")}
          </p>
        </div>
        <DreamButton lyceumId={d.id} onChanged={onDreamChanged} />
      </div>

      {description && <p className="whitespace-pre-line break-words text-ink">{description}</p>}

      {(dorm.dormitory_status ?? "unknown") !== "unknown" && (
        <section>
          <h3 className="mb-2 text-lg font-extrabold text-ink">{t("lyceums.dorm.title")}</h3>
          <DormitoryBadge status={dorm.dormitory_status} />
          {dormDescription && <p className="mt-2 whitespace-pre-line break-words text-ink">{dormDescription}</p>}
        </section>
      )}

      {p.gallery_urls.length > 0 && (
        <section aria-label={t("lyceums.gallery")}>
          <h3 className="mb-2 text-lg font-extrabold text-ink">{t("lyceums.gallery")}</h3>
          <ul className="flex max-w-full snap-x gap-2 overflow-x-auto pb-2">
            {p.gallery_urls.map((u) => (
              <li key={u} className="h-32 w-48 shrink-0 snap-start overflow-hidden rounded-2xl bg-snow sm:h-40 sm:w-60">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={mediaUrl(u)} alt="" loading="lazy" className="h-full w-full object-cover" />
              </li>
            ))}
          </ul>
        </section>
      )}

      {p.courses.length > 0 && (
        <section>
          <h3 className="mb-2 text-lg font-extrabold text-ink">{t("lyceums.courses")}</h3>
          <ul className="flex flex-wrap gap-2">
            {p.courses.map((x) => (
              <li key={x} className="rounded-full border-2 border-line px-3 py-1 text-sm font-bold text-ink">
                {x}
              </li>
            ))}
          </ul>
        </section>
      )}

      {hasContacts && (
        <section>
          <h3 className="mb-2 text-lg font-extrabold text-ink">{t("lyceums.contacts")}</h3>
          <ul className="flex flex-col gap-1 break-all text-ink">
            {p.website && (
              <li>
                <a href={safeHttp(p.website)} target="_blank" rel="noopener noreferrer" className="font-bold text-brand underline">
                  {p.website}
                </a>
              </li>
            )}
            {c.phone && (
              <li>
                <a href={`tel:${c.phone.replace(/\s/g, "")}`} className="font-bold text-brand underline">
                  {c.phone}
                </a>
              </li>
            )}
            {tg && (
              <li>
                <a href={tg} target="_blank" rel="noopener noreferrer" className="font-bold text-brand underline">
                  {c.telegram}
                </a>
              </li>
            )}
            {c.email && (
              <li>
                <a href={`mailto:${c.email}`} className="font-bold text-brand underline">
                  {c.email}
                </a>
              </li>
            )}
          </ul>
        </section>
      )}

      <AdmissionSeats admission={d.admission} />

      <PostsByKind posts={d.posts} />

      <section>
        <h3 className="mb-2 text-lg font-extrabold text-ink">{t("lyceums.stats")}</h3>
        <StatsTable detail={d} />
      </section>

      <p className="text-center text-sm text-ink-soft">
        <Link href="/rep/" className="underline hover:text-ink">
          {t("lyceums.representLink")}
        </Link>
      </p>
    </div>
  );
}
