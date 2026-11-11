import { api, type LyceumRow } from "./api";

/** `GET /v1/lyceums/fields` (public): edu.uz specialities with the subjects mapped to them. */
export const fetchFields = () => api.unwrap(api.client.GET("/v1/lyceums/fields"));
export type FieldRow = Awaited<ReturnType<typeof fetchFields>>[number];

/** Priority lyceums that do not offer `fieldCode` (never blocks saving; shown as a warning). */
export const mismatchIds = (ids: string[], rows: LyceumRow[], fieldCode: string | null): string[] => {
  if (!fieldCode) return [];
  const byId = new Map(rows.map((r) => [r.id, r]));
  return ids.filter((id) => {
    const r = byId.get(id);
    return r ? !r.field_codes.includes(fieldCode) : false;
  });
};
