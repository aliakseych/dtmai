"use client";
import { useEffect, useState } from "react";
import { useLocale } from "@dtmai/i18n";
import { api } from "@/lib/api";
import { useLearnLanguage } from "@/lib/auth";
import { contentLang } from "@/lib/localized";
import type { TheoryCard } from "./TheoryCards";

/** Theory cards of one lesson, read from the subject's learner path. `undefined` while loading; `[]` when there are none or the lookup failed. */
export function useLessonTheory(subjectId: string | null, lessonId: string | undefined): TheoryCard[] | undefined {
  const language = useLearnLanguage();
  const { locale } = useLocale();
  const [cards, setCards] = useState<TheoryCard[] | undefined>(subjectId && lessonId ? undefined : []);
  useEffect(() => {
    if (!subjectId || !lessonId) return setCards([]);
    let live = true;
    api
      .unwrap(api.client.GET("/v1/catalog/subjects/{subject_id}/path", { params: { path: { subject_id: subjectId }, query: { language, locale: contentLang(locale) } } }))
      .then(
        (p) => {
          const l = p.units.flatMap((u) => u.lessons).find((x) => x.id === lessonId);
          if (live) setCards(l?.has_theory ? (l.theory ?? []) : []);
        },
        () => live && setCards([]),
      );
    return () => {
      live = false;
    };
  }, [subjectId, lessonId, language, locale]);
  return cards;
}
