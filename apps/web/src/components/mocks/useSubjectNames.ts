"use client";
import { useCallback } from "react";
import { useLocale } from "@dtmai/i18n";
import { api } from "@/lib/api";
import { pick } from "@/lib/localized";
import { useAsync } from "@/lib/useAsync";

const load = () => api.unwrap(api.client.GET("/v1/catalog/subjects"));

/** Resolves a subject id to its localized name (empty until loaded). */
export function useSubjectNames() {
  const { locale } = useLocale();
  const { state } = useAsync(load, []);
  const subjects = state.status === "ready" ? state.data : [];
  const name = useCallback((id: string) => pick(subjects.find((s) => s.id === id)?.names, locale), [subjects, locale]);
  return { subjects, name };
}
