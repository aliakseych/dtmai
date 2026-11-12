"use client";
import { useCallback } from "react";
import { useLocale } from "@dtmai/i18n";
import { useSubjectNames } from "@/components/mocks/useSubjectNames";
import { fetchFields } from "@/lib/fields";
import { useAsync } from "@/lib/useAsync";

/**
 * Field (direction) label for a code: the API name is Uzbek-only, so for other locales the localized subject
 * pair is shown instead; the code itself is never the label.
 */
export function useFieldLabel() {
  const { locale } = useLocale();
  const { name: subjectName } = useSubjectNames();
  const { state } = useAsync(fetchFields, []);
  return useCallback(
    (code: string, fallback?: string): { name: string; subjects: string } => {
      const f = state.status === "ready" ? state.data.find((x) => x.code === code) : undefined;
      const subjects = f ? f.subject_ids.map((id) => subjectName(id)).filter(Boolean).join(" · ") : "";
      const uz = locale === "uz-Latn" || locale === "uz-Cyrl";
      const base = f?.name ?? fallback ?? "";
      return uz ? { name: base || code, subjects } : { name: subjects || base || code, subjects: "" };
    },
    [state, subjectName, locale],
  );
}
