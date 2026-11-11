"use client";
import type { components } from "@dtmai/api-client";
import { api } from "./api";

type S = components["schemas"];
export type GenerationRun = S["GenerationOut"];
export type GenerationIn = S["GenerationIn"];
const A = api.client;
const u = api.unwrap;

export const generation = {
  list: (limit = 100) => u(A.GET("/v1/admin/labeling/generation-runs", { params: { query: { limit } } })),
  start: (body: GenerationIn) => u(A.POST("/v1/admin/labeling/generation-runs", { body })),
  solve: (question_ids: string[]) => u(A.POST("/v1/admin/labeling/solve", { body: { question_ids } })),
};
