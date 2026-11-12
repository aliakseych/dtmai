"use client";
import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import { buttonClass } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import { DREAM_PLACEHOLDER } from "@/components/lyceums/LyceumMedia";
import { useLyceumDetail } from "@/components/lyceums/useLyceumDetail";
import { useAuth } from "@/lib/auth";
import { dreamIds } from "@/lib/dreams";
import { mediaUrl } from "@/lib/env";
import { fetchFields } from "@/lib/fields";
import { pick } from "@/lib/localized";
import { daysBetween, todayISO } from "@/lib/planDates";
import { getSettings } from "@/lib/planner";
import { useAsync } from "@/lib/useAsync";

/** Home identity card: "Future <lyceum> student, day N" with the lyceum's logo/cover; always changeable. */
export function DreamCard() {
  const t = useT();
  const { locale } = useLocale();
  const reduce = useReducedMotion();
  const { me } = useAuth();
  const first = dreamIds(me)[0];
  const { data } = useLyceumDetail(first);
  const settings = useAsync(getSettings, []);
  const fields = useAsync(fetchFields, []);

  if (!first) {
    return (
      <section className="flex flex-col gap-3 rounded-card border-2 border-line bg-white p-4 sm:flex-row sm:items-center">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={DREAM_PLACEHOLDER} alt="" className="h-24 w-32 shrink-0 self-center object-contain" />
        <div className="min-w-0 flex-1">
          <h2 className="break-words font-extrabold">{t("dream.card.empty")}</h2>
          <p className="text-sm text-ink-soft">{t("dream.card.emptyBody")}</p>
        </div>
        <Link href="/lyceums/" className={buttonClass("super")}>
          {t("dream.card.set")}
        </Link>
      </section>
    );
  }
  if (!data) return null;

  const name = pick(data.names, locale);
  const start = settings.state.status === "ready" ? settings.state.data?.start_date : null;
  const day = start ? Math.max(1, daysBetween(start, todayISO()) + 1) : null;
  const field =
    me?.field_code && fields.state.status === "ready" ? fields.state.data.find((f) => f.code === me.field_code)?.name : undefined;
  const photo = data.profile.campus_photo_url;
  const logo = data.profile.logo_url;

  return (
    <motion.section
      initial={reduce ? false : { y: 8, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="flex flex-wrap items-center gap-3 rounded-card border-2 border-line bg-brand p-4 text-white"
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={logo ? mediaUrl(logo) : photo ? mediaUrl(photo) : DREAM_PLACEHOLDER}
        alt=""
        className="h-16 w-16 shrink-0 rounded-2xl border-2 border-line bg-white object-contain p-1"
      />
      <div className="min-w-0 flex-1 basis-48">
        <h2 className="text-lg font-extrabold leading-tight [overflow-wrap:anywhere] [word-break:normal]">
          {day ? t("dream.card.title", { name, day }) : t("dream.card.titleNoDay", { name })}
        </h2>
        {field && <p className="break-words text-sm font-bold opacity-90">{t("dream.card.field", { name: field })}</p>}
      </div>
      <Link href="/lyceums/" className="ml-auto shrink-0 rounded-xl bg-white px-3 py-2 text-sm font-extrabold text-brand">
        {t("dream.card.change")}
      </Link>
    </motion.section>
  );
}
