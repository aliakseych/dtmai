import { api, type Me } from "./api";

export const MAX_DREAMS = 3;

/** Ordered dream-lyceum priority list (1st choice first). */
export const dreamIds = (me: Me | null | undefined): string[] => me?.dream_lyceum_ids ?? [];

/** PATCH /v1/identity/me { dream_lyceum_ids }. */
export const saveDreams = (ids: string[]) => api.unwrap(api.client.PATCH("/v1/identity/me", { body: { dream_lyceum_ids: ids } }));

export function moveItem<T>(list: readonly T[], from: number, to: number): T[] {
  const next = [...list];
  const [it] = next.splice(from, 1);
  next.splice(to, 0, it as T);
  return next;
}
