"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useLocale, useT } from "@dtmai/i18n";
import { pick } from "@/lib/localized";
import { PageTitle } from "@/components/PageTitle";
import { LyceumDetailView } from "./LyceumDetailView";
import { useLyceumDetail } from "./useLyceumDetail";

/** Deep-linkable lyceum page: /lyceum/?id=<uuid>. */
export function LyceumPage() {
  const t = useT();
  const { locale } = useLocale();
  const id = useSearchParams().get("id");
  const { data, reload } = useLyceumDetail(id);
  return (
    <div className="flex flex-col gap-4">
      <Link href="/lyceums/" className="inline-flex min-h-11 items-center self-start font-bold text-brand underline">
        {t("lyceums.backToList")}
      </Link>
      {data === undefined && <p className="py-4 text-center text-ink-soft">{t("common.loading")}</p>}
      {data === null && (
        <p role="alert" className="py-4 text-center text-ink-soft">
          {id ? t("common.error") : t("lyceums.notFound")}
        </p>
      )}
      {data && (
        <>
          <PageTitle>{pick(data.names, locale)}</PageTitle>
          <LyceumDetailView detail={data} onDreamChanged={reload} />
        </>
      )}
    </div>
  );
}
