"use client";
import type { components } from "@dtmai/api-client";
import { api } from "./api";

type S = components["schemas"];
export type ImportRun = S["ImportRunOut"];
export type LyceumRow = S["LyceumSummary"];
export type LyceumDetail = S["LyceumDetail"];
export type LyceumPatch = S["LyceumPatch"];
export type Membership = S["MembershipOut"];
export type Post = S["PostOut"];
const A = api.client;
const u = api.unwrap;

export const lyceums = {
  imports: (limit = 50) => u(A.GET("/v1/admin/lyceums/imports", { params: { query: { limit } } })),
  start: (year: number) => u(A.POST("/v1/admin/lyceums/import", { body: { year } })),
  setPassingScore: (stat_id: string, passing_score: number | null) =>
    u(A.PATCH("/v1/admin/lyceums/stats/{stat_id}", { params: { path: { stat_id } }, body: { passing_score } })),
  list: (q?: string) => u(A.GET("/v1/lyceums", { params: { query: { q: q || undefined, limit: 100 } } })),
  detail: (id: string) => u(A.GET("/v1/lyceums/{lyceum_id}", { params: { path: { lyceum_id: id } } })),
  patch: (id: string, body: LyceumPatch) => u(A.PATCH("/v1/admin/lyceums/{lyceum_id}", { params: { path: { lyceum_id: id } }, body })),
  applications: () => u(A.GET("/v1/admin/lyceums/rep/applications")),
  approve: (lyceum_id: string, user_id: string) => u(A.POST("/v1/admin/lyceums/{lyceum_id}/rep/{user_id}/approve", { params: { path: { lyceum_id, user_id } } })),
  reject: (lyceum_id: string, user_id: string) => u(A.POST("/v1/admin/lyceums/{lyceum_id}/rep/{user_id}/reject", { params: { path: { lyceum_id, user_id } } })),
  posts: (status: S["PostStatus"] = "pending") => u(A.GET("/v1/admin/lyceums/posts", { params: { query: { status, limit: 100 } } })),
  moderate: (post_id: string, action: "publish" | "reject", reason?: string) =>
    u(A.POST("/v1/admin/lyceums/posts/{post_id}/moderate", { params: { path: { post_id } }, body: { action, reason: reason || null } })),
};

