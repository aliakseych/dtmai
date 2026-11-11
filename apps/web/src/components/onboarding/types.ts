import type { LyceumRow } from "@/lib/api";

/** Lyceum list item; `city`, `logo_url`, `campus_photo_url` are optional API additions. */
export type OnbLyceum = LyceumRow & { city?: string | null; logo_url?: string | null; campus_photo_url?: string | null };

export const normCity = (s: string) => s.trim().toLowerCase();
