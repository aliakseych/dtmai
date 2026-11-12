import type { components } from "@dtmai/api-client";
import type { MessageKey } from "@dtmai/i18n";
import { api } from "@/lib/api";

type S = components["schemas"];
export type RepPost = S["PostOut"];
export type RepPostIn = S["PostIn"];
export type Membership = S["MembershipOut"];

export const POST_KINDS = ["announcement", "offer", "free_mock", "visit", "event", "alumni", "chat_link", "faculty"] as const;
export type PostKind = (typeof POST_KINDS)[number];
export const KIND_LABEL: Record<PostKind, MessageKey> = {
  announcement: "rep.kind.announcement",
  offer: "rep.kind.offer",
  free_mock: "rep.kind.free_mock",
  visit: "rep.kind.visit",
  event: "rep.kind.event",
  alumni: "rep.kind.alumni",
  chat_link: "rep.kind.chat_link",
  faculty: "rep.kind.faculty",
};
/** Kinds that are scheduled; the API rejects them without `starts_at`. */
export const NEEDS_START: readonly string[] = ["free_mock", "visit", "event"];
/** Kinds that are a link; the API rejects them without `link`. */
export const NEEDS_LINK: readonly string[] = ["chat_link"];

/** Body of `PATCH /v1/lyceums/{id}/rep/profile` (all fields optional). */
export type RepProfileIn = components["schemas"]["RepProfilePatch"];

const A = api.client;
const u = api.unwrap;
const path = (lyceum_id: string) => ({ params: { path: { lyceum_id } } });

export const rep = {
  apply: (id: string, note: string) => u(A.POST("/v1/lyceums/{lyceum_id}/rep/apply", { ...path(id), body: { note } })),
  membership: (id: string) => u(A.GET("/v1/lyceums/{lyceum_id}/rep/membership", path(id))),
  posts: (id: string) => u(A.GET("/v1/lyceums/{lyceum_id}/rep/posts", path(id))),
  create: (id: string, body: RepPostIn) => u(A.POST("/v1/lyceums/{lyceum_id}/rep/posts", { ...path(id), body })),
  update: (id: string, post_id: string, body: RepPostIn) =>
    u(A.PUT("/v1/lyceums/{lyceum_id}/rep/posts/{post_id}", { params: { path: { lyceum_id: id, post_id } }, body })),
  remove: (id: string, post_id: string) =>
    u(A.DELETE("/v1/lyceums/{lyceum_id}/rep/posts/{post_id}", { params: { path: { lyceum_id: id, post_id } } })),
  updateProfile: (id: string, body: RepProfileIn) =>
    u(A.PATCH("/v1/lyceums/{lyceum_id}/rep/profile", { ...path(id), body })),
};
