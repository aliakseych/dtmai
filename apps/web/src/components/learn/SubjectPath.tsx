"use client";
import { useLocale, useT } from "@dtmai/i18n";
import { AsyncView } from "@/components/AsyncView";
import { api, type Path } from "@/lib/api";
import { useLearnLanguage } from "@/lib/auth";
import { contentLang } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";
import { isCode } from "@/lib/errors";
import { UnitSection } from "./UnitSection";
import { useUnlockPop } from "./useUnlockPop";

/** Vertical Duolingo-style path of one subject: units (topics) top to bottom. */
export function SubjectPath({ subjectId }: { subjectId: string }) {
  const t = useT();
  const language = useLearnLanguage();
  const { locale } = useLocale();
  const { state, reload } = useAsync(
    () =>
      api
        .unwrap(api.client.GET("/v1/catalog/subjects/{subject_id}/path", { params: { path: { subject_id: subjectId }, query: { language, locale: contentLang(locale) } } }))
        // No published path yet for this subject/language: show the empty state, not an error.
        .catch((e: unknown): Path => {
          if (isCode(e, "not_found")) return { units: [] } as unknown as Path;
          throw e;
        }),
    [subjectId, language, locale],
  );
  return (
    <AsyncView state={state} onRetry={reload} isEmpty={(d) => d.units.length === 0} emptyText={t("learn.empty")}>
      {(path) => <Units path={path} />}
    </AsyncView>
  );
}

function Units({ path }: { path: Path }) {
  const fresh = useUnlockPop(path.units.flatMap((u) => u.lessons.filter((l) => l.progress.state !== "locked").map((l) => l.id)));
  return (
    <div className="flex flex-col gap-8">
      {path.units.map((u, i) => (
        <UnitSection key={u.id} unit={u} index={i} fresh={fresh} />
      ))}
    </div>
  );
}
