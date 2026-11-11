"use client";
import type { components } from "@dtmai/api-client";
import { api } from "./api";

type S = components["schemas"];
export type Batch = S["BatchOut"];
export type BatchDetail = S["BatchDetail"];
export type BatchIn = S["BatchIn"];
const A = api.client;
const u = api.unwrap;

export const ingestion = {
  list: (limit = 100) => u(A.GET("/v1/admin/ingestion/batches", { params: { query: { limit } } })),
  get: (batch_id: string) => u(A.GET("/v1/admin/ingestion/batches/{batch_id}", { params: { path: { batch_id } } })),
  start: (body: BatchIn) => u(A.POST("/v1/admin/ingestion/batches", { body })),
  rerun: (batch_id: string, include_unfinished: boolean) =>
    u(A.POST("/v1/admin/ingestion/batches/{batch_id}/rerun", { params: { path: { batch_id } }, body: { include_unfinished } })),
};
