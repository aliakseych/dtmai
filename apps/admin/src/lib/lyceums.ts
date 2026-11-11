"use client";
import type { components } from "@dtmai/api-client";
import { api } from "./api";

type S = components["schemas"];
export type ImportRun = S["ImportRunOut"];
const A = api.client;
const u = api.unwrap;

export const lyceums = {
  imports: (limit = 50) => u(A.GET("/v1/admin/lyceums/imports", { params: { query: { limit } } })),
  start: (year: number) => u(A.POST("/v1/admin/lyceums/import", { body: { year } })),
  setPassingScore: (stat_id: string, passing_score: number | null) =>
    u(A.PATCH("/v1/admin/lyceums/stats/{stat_id}", { params: { path: { stat_id } }, body: { passing_score } })),
};
