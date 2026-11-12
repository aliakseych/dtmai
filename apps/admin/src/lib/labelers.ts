"use client";
import type { components, operations } from "@dtmai/api-client";
import { api } from "./api";

type S = components["schemas"];
export type LabelerCreated = S["LabelerCreated"];
export type ActivityRow = S["ActivityOut"];
export type LeaderRow = S["LeaderboardRowOut"];
export type ActivityQuery = NonNullable<operations["labeling_admin_activity"]["parameters"]["query"]>;
export type ActivitySort = NonNullable<ActivityQuery["sort"]>;
export type LeaderQuery = NonNullable<operations["labeling_admin_leaderboard"]["parameters"]["query"]>;
export type LeaderSort = NonNullable<LeaderQuery["sort"]>;

const A = api.client;
const u = api.unwrap;
const clean = <T extends object>(q: T): T => Object.fromEntries(Object.entries(q).filter(([, v]) => v !== "" && v != null)) as T;

export const labelers = {
  create: (display_name?: string) => u(A.POST("/v1/admin/labelers", { body: { display_name: display_name || null } })),
  activity: (query: ActivityQuery) => u(A.GET("/v1/admin/labeling/activity", { params: { query: clean(query) } })),
  leaderboard: (query: LeaderQuery) => u(A.GET("/v1/admin/labeling/leaderboard", { params: { query: clean(query) } })),
};
